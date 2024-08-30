cmake_minimum_required(VERSION 3.25)

project(kiaukutas LANGUAGES CXX VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_FLAGS_RELEASE "-O3")

include(CheckLanguage)
check_language(CUDA)
if(CMAKE_CUDA_COMPILER)
  set(GGML_CUDA 1)
endif()

include(FetchContent)
FetchContent_Declare(llama.cpp
  GIT_REPOSITORY https://github.com/ggerganov/llama.cpp.git
  GIT_TAG b3645
)
FetchContent_MakeAvailable(llama.cpp)

add_executable(${PROJECT_NAME})

file(GLOB SRC_FILES CONFIGURE_DEPENDS src/*.cpp)

target_sources(${PROJECT_NAME} PUBLIC ${SRC_FILES})

target_link_libraries(${PROJECT_NAME}
  common
  llama
)
