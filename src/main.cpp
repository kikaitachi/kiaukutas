#include "audio.hpp"
#include "llm.hpp"
#include "http_server.hpp"

int main() {
  LLM("models/Meta-Llama-3.1-8B-Instruct-IQ4_XS.gguf");
  HTTPServer().serve(8000);
  return 0;
}
