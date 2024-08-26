#include <cstring>
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/sendfile.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <thread>
#include <unistd.h>

#include "http_server.hpp"
#include "logger.hpp"

HTTPServer::HTTPServer() {
}

void HTTPServer::serve(int port) {
  int server_fd = socket(AF_INET, SOCK_STREAM, 0);
  if (server_fd == -1) {
    throw std::runtime_error("Failed to create HTTP server socket");
  }
  int sock_option = 1;
  if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &sock_option, sizeof(sock_option)) == -1) {
    throw std::runtime_error("Can't enable SO_REUSEADDR option for HTTP server socket");
  }
  struct sockaddr_in addr;
  std::memset(&addr, '0', sizeof(addr));
  addr.sin_family = AF_INET;
  addr.sin_addr.s_addr = htonl(INADDR_ANY);
  addr.sin_port = htons(port);
  if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
    throw std::runtime_error("Failed to bind HTTP server socket");
  }
  if (listen(server_fd, 10) == -1) {
    throw std::runtime_error("Failed to listen to HTTP server socket");
  }
  logger::info("HTTP server started");
  for ( ; ; ) {
    struct sockaddr addr;
    socklen_t addr_len = sizeof(addr);
    int client_fd = accept(server_fd, &addr, &addr_len);
    if (client_fd == -1) {
      logger::last("Failed to accept connection on server socket %d", server_fd);
    } else {
      char host[INET6_ADDRSTRLEN];
      struct sockaddr_in* addr_in = (struct sockaddr_in*)&addr;
      inet_ntop(addr_in->sin_family, &addr_in->sin_addr, host, sizeof(host));
      logger::info("%s connected", host);
      std::thread accept_thread(&HTTPServer::client_handler, this, client_fd);
      accept_thread.detach();
    }
  }
}

void HTTPServer::client_handler(int fd) {
  struct timeval timeout;
  timeout.tv_sec = 5;
  timeout.tv_usec = 0;
  if (setsockopt (fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) < 0) {
    logger::last("Failed to set receive timeout for client socket %d", fd);
  }
  if (setsockopt (fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout)) < 0) {
    logger::last("Failed to set send timeout for client socket %d", fd);
  }
  char buf[1024 * 4];
  int len = 0;
  for ( ; ; ) {
    ssize_t result = read(fd, &buf[len], sizeof(buf) - len);
    if (result < 0) {
      logger::last("Failed to read from client socket %d", fd);
      break;
    }
    len += result;
    const std::string_view request(buf, len);
    if (request.starts_with("GET ") && request.find("\r") != std::string_view::npos) {
      std::size_t end = request.find(" ", 4);
      if (end != std::string_view::npos) {
        const std::string_view path = request.substr(4, end - 4);
        logger::info("Request for path %s from client socket %d", std::string(path).c_str(), fd);
        std::string file_name = "dist/index.html";
        if (path != "/") {
          file_name = "dist" + std::string(path);
        }
        std::string mime = "text/plain";
        if (file_name.ends_with(".html")) {
          mime = "text/html";
        } else if (file_name.ends_with(".js")) {
          mime = "text/javascript";
        } else if (file_name.ends_with(".css")) {
          mime = "text/css";
        } else if (file_name.ends_with(".svg")) {
          mime = "image/svg+xml";
        } else if (file_name.ends_with(".stl")) {
          mime = "model/stl";
        }
        result = snprintf(buf, sizeof(buf),
          "HTTP/1.1 200 OK\r\nContent-Type: %s\r\n\r\n",
          mime.c_str());
        if (result < 0 || result > sizeof(buf)) {
          logger::last("socket %d: failed generate response header", fd);
          break;
        }
        result = write(fd, buf, result);
        if (result < 0) {
          logger::last("socket %d: failed send response header", fd);
          break;
        }
        // TODO: check if all data was send

        int file = open(file_name.c_str(), O_RDONLY);
        if (file == -1) {
          logger::last(
            "socket %d: failed to open file '%s'",
            fd, file_name.c_str());
          break;
        }
        struct stat file_stat;
        if (fstat(file, &file_stat) == -1) {
          logger::last(
            "socket %d: failed to get size of file '%s'",
            fd, file_name.c_str());
          break;
        }
        off_t offset = 0;
        for ( ; ; ) {
          result = sendfile(fd, file, &offset, file_stat.st_size - offset);
          if (result == -1) {
            logger::last("socket %d: file %d: sendfile failed", fd, file);
            break;
          }
          if (offset == file_stat.st_size) {
            break;
          }
        }
        close(file);
        break;
      }
    }
    if (len == sizeof(buf)) {
      logger::error("HTTP request > %d for client socket %d", sizeof(buf), fd);
      break;
    }
  }
  close(fd);
}
