#include "audio.hpp"
#include "http_server.hpp"

int main() {
  HTTPServer().serve(8000);
  return 0;
}
