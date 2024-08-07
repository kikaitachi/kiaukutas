#ifndef SRC_HTTP_SERVER_HPP_
#define SRC_HTTP_SERVER_HPP_

class HTTPServer {
 public:
  HTTPServer();
  void serve(int port);
 private:
  void client_handler(int fd);
};

#endif  // SRC_HTTP_SERVER_HPP_
