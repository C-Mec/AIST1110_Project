
####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was PortMidiConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################

# The imported target's INTERFACE_LINK_LIBRARIES property contains targets
# provided by other CMake packages. Finding these dependencies is necessary
# for this config to be actually usable and selected, but they must not be
# looked with the REQUIRED keyword because this would raise an immediate error
# also when the user wants CMake to continue (other locations, custom script).
# https://cmake.org/cmake/help/latest/module/CMakeFindDependencyMacro.html

include(CMakeFindDependencyMacro)

if(UNIX AND NOT APPLE AND NOT HAIKU AND ( MATCHES ".*PMALSA.*"))
  find_dependency(ALSA)
endif()

if(NOT WIN32)
  set(THREADS_PREFER_PTHREAD_FLAG ON)
  find_dependency(Threads)
endif()

include("${CMAKE_CURRENT_LIST_DIR}/PortMidiTargets.cmake")

check_required_components(PortMidi)
