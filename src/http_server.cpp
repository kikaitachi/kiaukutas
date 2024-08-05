#include <arpa/inet.h>
#include <sys/socket.h>
#include <thread>

#include "http_server.hpp"
#include "logger.hpp"

HTTPServer::HTTPServer() {
  // std::thread accept_thread(&HTTPServer::accept_handler, this);
  // accept_thread.detach();
}

void HTTPServer::serve() {
  int server_fd = socket(AF_INET, SOCK_STREAM, 0);
  if (server_fd == -1) {
    throw std::runtime_error("Failed to create HTTP server socket");
  }
  int sock_option = 1;
  if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &sock_option, sizeof(sock_option)) == -1) {
    throw std::runtime_error("Can't enable SO_REUSEADDR option for HTTP server socket");
  }
  logger::info("HTTP server started");
}
