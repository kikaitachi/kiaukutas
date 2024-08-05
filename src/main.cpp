#include "audio.hpp"
#include "http_server.hpp"

int main() {
  HTTPServer().serve();
  return 0;
}
