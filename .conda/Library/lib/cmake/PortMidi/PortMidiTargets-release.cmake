#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "PortMidi::portmidi" for configuration "Release"
set_property(TARGET PortMidi::portmidi APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(PortMidi::portmidi PROPERTIES
  IMPORTED_IMPLIB_RELEASE "${_IMPORT_PREFIX}/lib/portmidi.lib"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/portmidi.dll"
  )

list(APPEND _cmake_import_check_targets PortMidi::portmidi )
list(APPEND _cmake_import_check_files_for_PortMidi::portmidi "${_IMPORT_PREFIX}/lib/portmidi.lib" "${_IMPORT_PREFIX}/bin/portmidi.dll" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
