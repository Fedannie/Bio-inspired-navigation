# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.26

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Disable VCS-based implicit rules.
% : %,v

# Disable VCS-based implicit rules.
% : RCS/%

# Disable VCS-based implicit rules.
% : RCS/%,v

# Disable VCS-based implicit rules.
% : SCCS/s.%

# Disable VCS-based implicit rules.
% : s.%

.SUFFIXES: .hpux_make_needs_suffix_list

# Command-line flag to silence nested $(MAKE).
$(VERBOSE)MAKESILENT = -s

#Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/local/Cellar/cmake/3.26.4/bin/cmake

# The command to remove a file.
RM = /usr/local/Cellar/cmake/3.26.4/bin/cmake -E rm -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/src

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/build

# Utility rule file for clean_test_results_roswtf.

# Include any custom commands dependencies for this target.
include ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf.dir/compiler_depend.make

# Include the progress variables for this target.
include ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf.dir/progress.make

ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf:
	cd /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/build/ros_comm/roswtf && /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/venv/bin/python /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/src/catkin/cmake/test/remove_test_results.py /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/build/test_results/roswtf

clean_test_results_roswtf: ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf
clean_test_results_roswtf: ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf.dir/build.make
.PHONY : clean_test_results_roswtf

# Rule to build all files generated by this target.
ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf.dir/build: clean_test_results_roswtf
.PHONY : ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf.dir/build

ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf.dir/clean:
	cd /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/build/ros_comm/roswtf && $(CMAKE_COMMAND) -P CMakeFiles/clean_test_results_roswtf.dir/cmake_clean.cmake
.PHONY : ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf.dir/clean

ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf.dir/depend:
	cd /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/src /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/src/ros_comm/roswtf /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/build /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/build/ros_comm/roswtf /Users/anna/Documents/TUM/Thesis/ba-bio-inspired-navigation-main/range_libc/pywrapper/ros/build/ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : ros_comm/roswtf/CMakeFiles/clean_test_results_roswtf.dir/depend
