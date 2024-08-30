#include "llm.hpp"
#include "llama.h"
#include "logger.hpp"

#include "cstring"

static void log_callback(enum ggml_log_level level, const char *text, void *user_data) {
  size_t len = strlen(text);
  if (len > 2) {  // Ignore logging like "." or just new lines
    logger::debug("llm: %.*s", len - 1, text);
  }
}

LLM::LLM(std::string file) {
  llama_log_set(log_callback, nullptr);
  llama_model_params mparams = llama_model_default_params();
  llama_model *lmodel = llama_load_model_from_file(file.c_str(), mparams);
}
