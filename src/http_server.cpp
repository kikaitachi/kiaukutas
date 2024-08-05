#include <cstring>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <thread>

#include "http_server.hpp"
#include "logger.hpp"

HTTPServer::HTTPServer() {
  // std::thread accept_thread(&HTTPServer::accept_handler, this);
  // accept_thread.detach();
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
      // TODO: create new thread
    }
  }
}
