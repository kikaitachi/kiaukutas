#include "common.h"
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
  llama_context_params cparams = llama_context_default_params();
  llama_context *ctx = llama_new_context_with_model(lmodel, cparams);
  if (ctx == NULL) {
      logger::error("Failed to create llama context");
      llama_free_model(lmodel);
      return;
  }
  // llama_token token = llama_add_bos_token(lmodel);
  llama_token tokens[1024];
  std::string prompt = // <|begin_of_text|>
    "<|start_header_id|>system<|end_header_id|>\n"
    "You are a helpful assistant<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
    "What is the capital of France?<|eot_id|>\n"
    "<|start_header_id|>assistant<|end_header_id|>";
  int32_t token_count = llama_tokenize(
    lmodel,
    prompt.c_str(),
    prompt.size(),
    tokens,
    1024,
    true,true
  );
  logger::info("Tokenized %d character prompt to %d tokens", prompt.size(), token_count);

  llama_batch batch = llama_batch_init(512, 0, 1);
  for (size_t i = 0; i < token_count; i++) {
    llama_batch_add(batch, tokens[i], i, { 0 }, false);
  }
  // llama_decode will output logits only for the last token of the prompt
  batch.logits[batch.n_tokens - 1] = true;

  if (llama_decode(ctx, batch) != 0) {
    logger::error("llama failed to decode");
  }

  int n_cur = batch.n_tokens;
  int n_decode = 0;
  const int n_predict = 512;

  while (n_cur <= n_predict) {
    auto   n_vocab = llama_n_vocab(lmodel);
    auto * logits  = llama_get_logits_ith(ctx, batch.n_tokens - 1);

    std::vector<llama_token_data> candidates;
    candidates.reserve(n_vocab);

    for (llama_token token_id = 0; token_id < n_vocab; token_id++) {
      candidates.emplace_back(llama_token_data{ token_id, logits[token_id], 0.0f });
    }

    llama_token_data_array candidates_p = { candidates.data(), candidates.size(), false };

    // sample the most likely token
    const llama_token new_token_id = llama_sample_token_greedy(ctx, &candidates_p);

    // is it an end of generation?
    if (llama_token_is_eog(lmodel, new_token_id) || n_cur == n_predict) {
        logger::info("end of generation");
        break;
    }

    logger::info("Got piece: %s", llama_token_to_piece(ctx, new_token_id).c_str());

    // prepare the next batch
    llama_batch_clear(batch);

    // push this new token for next evaluation
    llama_batch_add(batch, new_token_id, n_cur, { 0 }, true);

    n_decode += 1;

    n_cur += 1;

    // evaluate the current batch with the transformer model
    if (llama_decode(ctx, batch)) {
        logger::error("llama failed to decode not first batch");
        return;
    }
  }
}
