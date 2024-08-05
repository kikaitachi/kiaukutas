#ifndef SRC_LOGGER_HPP_
#define SRC_LOGGER_HPP_

#include <string>

namespace logger {
  /**
   * Log a message with a debug level.
   */
  void debug(const std::string format, ...);

  /**
   * Log a message with a info level.
   */
  void info(const std::string format, ...);

  /**
   * Log a message with a warning level.
   */
  void warn(const std::string format, ...);

  /**
   * Log a message with a error level.
   */
  void error(const std::string format, ...);

  /**
   * Log a message with a error level and append error from the last call.
   */
  void last(const std::string format, ...);
}

#endif  // SRC_LOGGER_HPP_
