 ###############################################################
 # 
 # Copyright 2011 Red Hat, Inc. 
 # 
 # Licensed under the Apache License, Version 2.0 (the "License"); you 
 # may not use this file except in compliance with the License.  You may 
 # obtain a copy of the License at 
 # 
 #    http://www.apache.org/licenses/LICENSE-2.0 
 # 
 # Unless required by applicable law or agreed to in writing, software 
 # distributed under the License is distributed on an "AS IS" BASIS, 
 # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 # See the License for the specific language governing permissions and 
 # limitations under the License. 
 # 
 ############################################################### 


MACRO ( GSOAP_GEN _DAEMON _HDRS _SRCS )

if ( HAVE_EXT_GSOAP )

	set ( ${_DAEMON}_SOAP_SRCS
		soap_${_DAEMON}C.cpp
		soap_${_DAEMON}Server.cpp)

	set ( ${_DAEMON}_SOAP_ENV
		soap_env_${_DAEMON}C.cpp )

	set ( ${_DAEMON}_SOAP_HDRS
		soap_${_DAEMON}H.h
		soap_${_DAEMON}Stub.h )
		
	if (WINDOWS)
	  set(ISEP "\;")
	else()
	  set(ISEP :)
	endif()
	
	#dprint("ISEP=${ISEP}")

	#TODO update all the output targets so clean will 
	#remove all soap generated things.  
	add_custom_command(
		OUTPUT ${${_DAEMON}_SOAP_SRCS} ${${_DAEMON}_SOAP_HDRS} condor.xsd
		COMMAND ${SOAPCPP2}
		ARGS -I${DAEMON_CORE}${ISEP}${CMAKE_CURRENT_SOURCE_DIR} -S -L -x -q soap_${_DAEMON} -p soap_${_DAEMON} ${CMAKE_CURRENT_SOURCE_DIR}/gsoap_${_DAEMON}.h
		COMMENT "Generating ${_DAEMON} soap files" )

	# libgsoap++ will look for some global symbols (_soap_faultsubcode, for example) that are not
	# generated by the above line as we now use C++ namespaces.  Hence, we generate the global
	# symbols by creating an empty soap project.  NOTE that we do not add the new header to the
	# daemon's header; this is because nothing will actually use that header.
	add_custom_command(
		OUTPUT ${${_DAEMON}_SOAP_ENV}
		COMMAND ${SOAPCPP2}
		ARGS -psoap_env_${_DAEMON} -S -L -x ${CMAKE_CURRENT_SOURCE_DIR}/../condor_daemon_core.V6/soapEnv.h
		COMMENT "Generating ${_DAEMON} soap dependencies" )

	add_custom_target(
			gen_${_DAEMON}_soapfiles
			ALL
			DEPENDS ${${_DAEMON}_SOAP_SRCS} ${${_DAEMON}_SOAP_ENV} )
			
	if (NOT PROPER AND GSOAP_REF)
		add_dependencies( gen_${_DAEMON}_soapfiles ${GSOAP_REF} )
	endif()
	
	if (WINDOWS)
		set_property( TARGET gen_${_DAEMON}_soapfiles PROPERTY FOLDER "executables" )
	endif()	

	# now append the header and srcs to incoming vars
	if ( NOT ${_SRCS} MATCHES "soap_${_DAEMON}C.cpp" )
		list(APPEND ${_SRCS} ${${_DAEMON}_SOAP_SRCS} ${${_DAEMON}_SOAP_ENV} )
		list(APPEND ${_HDRS} ${${_DAEMON}_SOAP_HDRS} )
	endif()

	#  The generated files spew no end of warnings which we can't fix.
	#  So, turn off the warnings for these files. (-w means no warnings)
	if (UNIX)
		set_source_files_properties( soap_${_DAEMON}Stub.cpp ${${_DAEMON}_SOAP_SRCS} ${${_DAEMON}_SOAP_ENV} PROPERTIES COMPILE_FLAGS "-w")
	endif(UNIX)

	 list(REMOVE_DUPLICATES ${_SRCS})
	
endif()

ENDMACRO ( GSOAP_GEN )