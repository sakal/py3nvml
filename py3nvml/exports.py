#####
# Copyright (c) 2011-2015, NVIDIA Corporation.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the NVIDIA Corporation nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
#####

##
# Python bindings for the NVML library
##
from ctypes import *    # noqa
from .types import *
from .types import (_nvmlEnableState_t, _nvmlClockType_t, _nvmlTemperatureSensors_t,
    _nvmlTemperatureThresholds_t, _nvmlPstates_t, _nvmlGpuOperationMode_t,
    _nvmlComputeMode_t, _nvmlDriverModel_t, _nvmlPageRetirementCause_t,
    _nvmlPcieUtilCounter_t, _nvmlGpuTopologyLevel_t, _nvmlBrandType_t,
    _nvmlInforomObject_t)
from .util import bytes_to_str, nvmlStructToFriendlyObject
from .exceptions import NVMLError
import sys
import os

class NVML(object):

    ## C function wrappers ##
    def __init__(self):
        # Function access #
        self.__nvmlGetFunctionPointer_cache = dict() # function pointers are cached to prevent unnecessary
        self.__nvmlLib = None

        self.__LoadNvmlLibrary()

        #
        # Initialize the library
        #
        fn = self.__nvmlGetFunctionPointer("nvmlInit_v2")
        ret = fn()
        self.__nvmlCheckReturn(ret)

    def __nvmlCheckReturn(self, ret):
        if (ret != NVML_SUCCESS):
            raise NVMLError(ret)
        return ret

    def __nvmlGetFunctionPointer(self, name):
        if name in self.__nvmlGetFunctionPointer_cache:
            return self.__nvmlGetFunctionPointer_cache[name]

        # ensure library was loaded
        if (self.__nvmlLib == None):
            raise NVMLError(NVML_ERROR_UNINITIALIZED)
        try:
            self.__nvmlGetFunctionPointer_cache[name] = getattr(self.__nvmlLib, name)
            return self.__nvmlGetFunctionPointer_cache[name]
        except AttributeError:
            raise NVMLError(NVML_ERROR_FUNCTION_NOT_FOUND)

    def __LoadNvmlLibrary(self):
        '''
        Load the library if it isn't loaded already
        '''

        if (self.__nvmlLib == None):
            # ensure the library still isn't loaded
            if (self.__nvmlLib == None):
                try:
                    if (sys.platform[:3] == "win"):
                        # cdecl calling convention
                        # load nvml.dll from %ProgramFiles%/NVIDIA Corporation/NVSMI/nvml.dll
                        self.__nvmlLib = CDLL(os.path.join(os.getenv("ProgramFiles", "C:/Program Files"), "NVIDIA Corporation/NVSMI/nvml.dll"))
                    else:
                        # assume linux
                        self.__nvmlLib = CDLL("libnvidia-ml.so.1")
                except OSError as ose:
                    self.__nvmlCheckReturn(NVML_ERROR_LIBRARY_NOT_FOUND)
                if (self.__nvmlLib == None):
                    self.__nvmlCheckReturn(NVML_ERROR_LIBRARY_NOT_FOUND)

    def __del__(self):
        #
        # Leave the library loaded, but shutdown the interface
        #
        fn = self.__nvmlGetFunctionPointer("nvmlShutdown")
        ret = fn()
        self.__nvmlCheckReturn(ret)

        return None

    # Added in 2.285
    def nvmlErrorString(self, result):
        fn = self.__nvmlGetFunctionPointer("nvmlErrorString")
        fn.restype = c_char_p # otherwise return is an int
        ret = fn(result)
        return bytes_to_str(ret)

    # Added in 2.285
    def nvmlSystemGetNVMLVersion(self):
        c_version = create_string_buffer(NVML_SYSTEM_NVML_VERSION_BUFFER_SIZE)
        fn = self.__nvmlGetFunctionPointer("nvmlSystemGetNVMLVersion")
        ret = fn(c_version, c_uint(NVML_SYSTEM_NVML_VERSION_BUFFER_SIZE))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_version.value)

    # Added in 2.285
    def nvmlSystemGetProcessName(self, pid):
        c_name = create_string_buffer(1024)
        fn = self.__nvmlGetFunctionPointer("nvmlSystemGetProcessName")
        ret = fn(c_uint(pid), c_name, c_uint(1024))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_name.value)

    def nvmlSystemGetDriverVersion(self):
        c_version = create_string_buffer(NVML_SYSTEM_DRIVER_VERSION_BUFFER_SIZE)
        fn = self.__nvmlGetFunctionPointer("nvmlSystemGetDriverVersion")
        ret = fn(c_version, c_uint(NVML_SYSTEM_DRIVER_VERSION_BUFFER_SIZE))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_version.value)

    # Added in 2.285
    def nvmlSystemGetHicVersion(self):
        c_count = c_uint(0)
        hics = None
        fn = self.__nvmlGetFunctionPointer("nvmlSystemGetHicVersion")

        # get the count
        ret = fn(byref(c_count), None)

        # this should only fail with insufficient size
        if ((ret != NVML_SUCCESS) and
            (ret != NVML_ERROR_INSUFFICIENT_SIZE)):
            raise NVMLError(ret)

        # if there are no hics
        if (c_count.value == 0):
            return []

        hic_array = c_nvmlHwbcEntry_t * c_count.value
        hics = hic_array()
        ret = fn(byref(c_count), hics)
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(hics)


    ## Unit get functions
    def nvmlUnitGetCount(self):
        c_count = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlUnitGetCount")
        ret = fn(byref(c_count))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_count.value)

    def nvmlUnitGetHandleByIndex(self, index):
        c_index = c_uint(index)
        unit = c_nvmlUnit_t()
        fn = self.__nvmlGetFunctionPointer("nvmlUnitGetHandleByIndex")
        ret = fn(c_index, byref(unit))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(unit)

    def nvmlUnitGetUnitInfo(self, unit):
        c_info = c_nvmlUnitInfo_t()
        fn = self.__nvmlGetFunctionPointer("nvmlUnitGetUnitInfo")
        ret = fn(unit, byref(c_info))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_info)

    def nvmlUnitGetLedState(self, unit):
        c_state =  c_nvmlLedState_t()
        fn = self.__nvmlGetFunctionPointer("nvmlUnitGetLedState")
        ret = fn(unit, byref(c_state))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_state)

    def nvmlUnitGetPsuInfo(self, unit):
        c_info = c_nvmlPSUInfo_t()
        fn = self.__nvmlGetFunctionPointer("nvmlUnitGetPsuInfo")
        ret = fn(unit, byref(c_info))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_info)

    def nvmlUnitGetTemperature(self, unit, type):
        c_temp = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlUnitGetTemperature")
        ret = fn(unit, c_uint(type), byref(c_temp))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_temp.value)

    def nvmlUnitGetFanSpeedInfo(self, unit):
        c_speeds = c_nvmlUnitFanSpeeds_t()
        fn = self.__nvmlGetFunctionPointer("nvmlUnitGetFanSpeedInfo")
        ret = fn(unit, byref(c_speeds))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_speeds)

    # added to API
    def nvmlUnitGetDeviceCount(self, unit):
        c_count = c_uint(0)
        # query the unit to determine device count
        fn = self.__nvmlGetFunctionPointer("nvmlUnitGetDevices")
        ret = fn(unit, byref(c_count), None)
        if (ret == NVML_ERROR_INSUFFICIENT_SIZE):
            ret = NVML_SUCCESS
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_count.value)

    def nvmlUnitGetDevices(self, unit):
        c_count = c_uint(nvmlUnitGetDeviceCount(unit))
        device_array = c_nvmlDevice_t * c_count.value
        c_devices = device_array()
        fn = self.__nvmlGetFunctionPointer("nvmlUnitGetDevices")
        ret = fn(unit, byref(c_count), c_devices)
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_devices)

    ## Device get functions
    def nvmlDeviceGetCount(self):
        c_count = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetCount_v2")
        ret = fn(byref(c_count))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_count.value)

    def nvmlDeviceGetHandleByIndex(self, index):
        c_index = c_uint(index)
        device = c_nvmlDevice_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetHandleByIndex_v2")
        ret = fn(c_index, byref(device))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(device)

    def nvmlDeviceGetHandleBySerial(self, serial):
        c_serial = c_char_p(serial)
        device = c_nvmlDevice_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetHandleBySerial")
        ret = fn(c_serial, byref(device))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(device)

    def nvmlDeviceGetHandleByUUID(self, uuid):
        c_uuid = c_char_p(uuid)
        device = c_nvmlDevice_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetHandleByUUID")
        ret = fn(c_uuid, byref(device))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(device)

    def nvmlDeviceGetHandleByPciBusId(self, pciBusId):
        c_busId = c_char_p(pciBusId)
        device = c_nvmlDevice_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetHandleByPciBusId_v2")
        ret = fn(c_busId, byref(device))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(device)

    def nvmlDeviceGetName(self, handle):
        c_name = create_string_buffer(NVML_DEVICE_NAME_BUFFER_SIZE)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetName")
        ret = fn(handle, c_name, c_uint(NVML_DEVICE_NAME_BUFFER_SIZE))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_name.value)

    def nvmlDeviceGetBoardId(self, handle):
        c_id = c_uint();
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetBoardId")
        ret = fn(handle, byref(c_id))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_id.value)

    def nvmlDeviceGetMultiGpuBoard(self, handle):
        c_multiGpu = c_uint();
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetMultiGpuBoard")
        ret = fn(handle, byref(c_multiGpu))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_multiGpu.value)

    def nvmlDeviceGetBrand(self, handle):
        c_type = _nvmlBrandType_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetBrand")
        ret = fn(handle, byref(c_type))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_type.value)

    def nvmlDeviceGetSerial(self, handle):
        c_serial = create_string_buffer(NVML_DEVICE_SERIAL_BUFFER_SIZE)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetSerial")
        ret = fn(handle, c_serial, c_uint(NVML_DEVICE_SERIAL_BUFFER_SIZE))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_serial.value)

    def nvmlDeviceGetCpuAffinity(self, handle, cpuSetSize):
        affinity_array = c_ulonglong * cpuSetSize
        c_affinity = affinity_array()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetCpuAffinity")
        ret = fn(handle, cpuSetSize, byref(c_affinity))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_affinity)

    def nvmlDeviceSetCpuAffinity(self, handle):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetCpuAffinity")
        ret = fn(handle)
        self.__nvmlCheckReturn(ret)
        return None

    def nvmlDeviceClearCpuAffinity(self, handle):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceClearCpuAffinity")
        ret = fn(handle)
        self.__nvmlCheckReturn(ret)
        return None

    def nvmlDeviceGetMinorNumber(self, handle):
        c_minor_number = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetMinorNumber")
        ret = fn(handle, byref(c_minor_number))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_minor_number.value)

    def nvmlDeviceGetUUID(self, handle):
        c_uuid = create_string_buffer(NVML_DEVICE_UUID_BUFFER_SIZE)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetUUID")
        ret = fn(handle, c_uuid, c_uint(NVML_DEVICE_UUID_BUFFER_SIZE))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_uuid.value)

    def nvmlDeviceGetInforomVersion(self, handle, infoRomObject):
        c_version = create_string_buffer(NVML_DEVICE_INFOROM_VERSION_BUFFER_SIZE)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetInforomVersion")
        ret = fn(handle, _nvmlInforomObject_t(infoRomObject),
                 c_version, c_uint(NVML_DEVICE_INFOROM_VERSION_BUFFER_SIZE))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_version.value)

    # Added in 4.304
    def nvmlDeviceGetInforomImageVersion(self, handle):
        c_version = create_string_buffer(NVML_DEVICE_INFOROM_VERSION_BUFFER_SIZE)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetInforomImageVersion")
        ret = fn(handle, c_version, c_uint(NVML_DEVICE_INFOROM_VERSION_BUFFER_SIZE))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_version.value)

    # Added in 4.304
    def nvmlDeviceGetInforomConfigurationChecksum(self, handle):
        c_checksum = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetInforomConfigurationChecksum")
        ret = fn(handle, byref(c_checksum))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_checksum.value)

    # Added in 4.304
    def nvmlDeviceValidateInforom(self, handle):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceValidateInforom")
        ret = fn(handle)
        self.__nvmlCheckReturn(ret)
        return None

    def nvmlDeviceGetDisplayMode(self, handle):
        c_mode = _nvmlEnableState_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetDisplayMode")
        ret = fn(handle, byref(c_mode))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_mode.value)

    def nvmlDeviceGetDisplayActive(self, handle):
        c_mode = _nvmlEnableState_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetDisplayActive")
        ret = fn(handle, byref(c_mode))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_mode.value)

    def nvmlDeviceGetPersistenceMode(self, handle):
        c_state = _nvmlEnableState_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPersistenceMode")
        ret = fn(handle, byref(c_state))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_state.value)

    def nvmlDeviceGetPciInfo(self, handle):
        c_info = nvmlPciInfo_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPciInfo_v2")
        ret = fn(handle, byref(c_info))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_info)

    def nvmlDeviceGetClockInfo(self, handle, type):
        c_clock = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetClockInfo")
        ret = fn(handle, _nvmlClockType_t(type), byref(c_clock))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_clock.value)

    # Added in 2.285
    def nvmlDeviceGetMaxClockInfo(self, handle, type):
        c_clock = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetMaxClockInfo")
        ret = fn(handle, _nvmlClockType_t(type), byref(c_clock))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_clock.value)

    # Added in 4.304
    def nvmlDeviceGetApplicationsClock(self, handle, type):
        c_clock = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetApplicationsClock")
        ret = fn(handle, _nvmlClockType_t(type), byref(c_clock))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_clock.value)

    # Added in 5.319
    def nvmlDeviceGetDefaultApplicationsClock(self, handle, type):
        c_clock = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetDefaultApplicationsClock")
        ret = fn(handle, _nvmlClockType_t(type), byref(c_clock))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_clock.value)

    # Added in 4.304
    def nvmlDeviceGetSupportedMemoryClocks(self, handle):
        # first call to get the size
        c_count = c_uint(0)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetSupportedMemoryClocks")
        ret = fn(handle, byref(c_count), None)

        if (ret == NVML_SUCCESS):
            # special case, no clocks
            return []
        elif (ret == NVML_ERROR_INSUFFICIENT_SIZE):
            # typical case
            clocks_array = c_uint * c_count.value
            c_clocks = clocks_array()

            # make the call again
            ret = fn(handle, byref(c_count), c_clocks)
            self.__nvmlCheckReturn(ret)

            procs = []
            for i in range(c_count.value):
                procs.append(c_clocks[i])

            return procs
        else:
            # error case
            raise NVMLError(ret)

    # Added in 4.304
    def nvmlDeviceGetSupportedGraphicsClocks(self, handle, memoryClockMHz):
        # first call to get the size
        c_count = c_uint(0)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetSupportedGraphicsClocks")
        ret = fn(handle, c_uint(memoryClockMHz), byref(c_count), None)

        if (ret == NVML_SUCCESS):
            # special case, no clocks
            return []
        elif (ret == NVML_ERROR_INSUFFICIENT_SIZE):
            # typical case
            clocks_array = c_uint * c_count.value
            c_clocks = clocks_array()

            # make the call again
            ret = fn(handle, c_uint(memoryClockMHz), byref(c_count), c_clocks)
            self.__nvmlCheckReturn(ret)

            procs = []
            for i in range(c_count.value):
                procs.append(c_clocks[i])

            return procs
        else:
            # error case
            raise NVMLError(ret)

    def nvmlDeviceGetFanSpeed(self, handle):
        c_speed = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetFanSpeed")
        ret = fn(handle, byref(c_speed))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_speed.value)

    def nvmlDeviceGetTemperature(self, handle, sensor):
        c_temp = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetTemperature")
        ret = fn(handle, _nvmlTemperatureSensors_t(sensor), byref(c_temp))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_temp.value)

    def nvmlDeviceGetTemperatureThreshold(self, handle, threshold):
        c_temp = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetTemperatureThreshold")
        ret = fn(handle, _nvmlTemperatureThresholds_t(threshold), byref(c_temp))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_temp.value)

    # DEPRECATED use nvmlDeviceGetPerformanceState
    def nvmlDeviceGetPowerState(self, handle):
        c_pstate = _nvmlPstates_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPowerState")
        ret = fn(handle, byref(c_pstate))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_pstate.value)

    def nvmlDeviceGetPerformanceState(self, handle):
        c_pstate = _nvmlPstates_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPerformanceState")
        ret = fn(handle, byref(c_pstate))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_pstate.value)

    def nvmlDeviceGetPowerManagementMode(self, handle):
        c_pcapMode = _nvmlEnableState_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPowerManagementMode")
        ret = fn(handle, byref(c_pcapMode))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_pcapMode.value)

    def nvmlDeviceGetPowerManagementLimit(self, handle):
        c_limit = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPowerManagementLimit")
        ret = fn(handle, byref(c_limit))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_limit.value)

    # Added in 4.304
    def nvmlDeviceGetPowerManagementLimitConstraints(self, handle):
        c_minLimit = c_uint()
        c_maxLimit = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPowerManagementLimitConstraints")
        ret = fn(handle, byref(c_minLimit), byref(c_maxLimit))
        self.__nvmlCheckReturn(ret)
        return [c_minLimit.value, c_maxLimit.value]

    # Added in 4.304
    def nvmlDeviceGetPowerManagementDefaultLimit(self, handle):
        c_limit = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPowerManagementDefaultLimit")
        ret = fn(handle, byref(c_limit))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_limit.value)


    # Added in 331
    def nvmlDeviceGetEnforcedPowerLimit(self, handle):
        c_limit = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetEnforcedPowerLimit")
        ret = fn(handle, byref(c_limit))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_limit.value)

    def nvmlDeviceGetPowerUsage(self, handle):
        c_watts = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPowerUsage")
        ret = fn(handle, byref(c_watts))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_watts.value)

    # Added in 4.304
    def nvmlDeviceGetGpuOperationMode(self, handle):
        c_currState = _nvmlGpuOperationMode_t()
        c_pendingState = _nvmlGpuOperationMode_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetGpuOperationMode")
        ret = fn(handle, byref(c_currState), byref(c_pendingState))
        self.__nvmlCheckReturn(ret)
        return [c_currState.value, c_pendingState.value]

    # Added in 4.304
    def nvmlDeviceGetCurrentGpuOperationMode(self, handle):
        return self.nvmlDeviceGetGpuOperationMode(handle)[0]

    # Added in 4.304
    def nvmlDeviceGetPendingGpuOperationMode(self, handle):
        return self.nvmlDeviceGetGpuOperationMode(handle)[1]

    def nvmlDeviceGetMemoryInfo(self, handle):
        c_memory = c_nvmlMemory_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetMemoryInfo")
        ret = fn(handle, byref(c_memory))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_memory)

    def nvmlDeviceGetBAR1MemoryInfo(self, handle):
        c_bar1_memory = c_nvmlBAR1Memory_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetBAR1MemoryInfo")
        ret = fn(handle, byref(c_bar1_memory))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_bar1_memory)

    def nvmlDeviceGetComputeMode(self, handle):
        c_mode = _nvmlComputeMode_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetComputeMode")
        ret = fn(handle, byref(c_mode))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_mode.value)

    def nvmlDeviceGetEccMode(self, handle):
        c_currState = _nvmlEnableState_t()
        c_pendingState = _nvmlEnableState_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetEccMode")
        ret = fn(handle, byref(c_currState), byref(c_pendingState))
        self.__nvmlCheckReturn(ret)
        return [c_currState.value, c_pendingState.value]

    # added to API
    def nvmlDeviceGetCurrentEccMode(self, handle):
        return self.nvmlDeviceGetEccMode(handle)[0]

    # added to API
    def nvmlDeviceGetPendingEccMode(self, handle):
        return self.nvmlDeviceGetEccMode(handle)[1]

    def nvmlDeviceGetTotalEccErrors(self, handle, errorType, counterType):
        c_count = c_ulonglong()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetTotalEccErrors")
        ret = fn(handle, _nvmlMemoryErrorType_t(errorType),
                 _nvmlEccCounterType_t(counterType), byref(c_count))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_count.value)

    # This is deprecated, instead use nvmlDeviceGetMemoryErrorCounter
    def nvmlDeviceGetDetailedEccErrors(self, handle, errorType, counterType):
        c_counts = c_nvmlEccErrorCounts_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetDetailedEccErrors")
        ret = fn(handle, _nvmlMemoryErrorType_t(errorType),
                 _nvmlEccCounterType_t(counterType), byref(c_counts))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_counts)

    # Added in 4.304
    def nvmlDeviceGetMemoryErrorCounter(self, handle, errorType, counterType, locationType):
        c_count = c_ulonglong()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetMemoryErrorCounter")
        ret = fn(handle,
                _nvmlMemoryErrorType_t(errorType),
                _nvmlEccCounterType_t(counterType),
                _nvmlMemoryLocation_t(locationType),
                byref(c_count))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_count.value)

    def nvmlDeviceGetUtilizationRates(self, handle):
        c_util = c_nvmlUtilization_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetUtilizationRates")
        ret = fn(handle, byref(c_util))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_util)

    def nvmlDeviceGetEncoderUtilization(self, handle):
        c_util = c_uint()
        c_samplingPeriod = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetEncoderUtilization")
        ret = fn(handle, byref(c_util), byref(c_samplingPeriod))
        self.__nvmlCheckReturn(ret)
        return [c_util.value, c_samplingPeriod.value]

    def nvmlDeviceGetDecoderUtilization(self, handle):
        c_util = c_uint()
        c_samplingPeriod = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetDecoderUtilization")
        ret = fn(handle, byref(c_util), byref(c_samplingPeriod))
        self.__nvmlCheckReturn(ret)
        return [c_util.value, c_samplingPeriod.value]

    def nvmlDeviceGetPcieReplayCounter(self, handle):
        c_replay = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPcieReplayCounter")
        ret = fn(handle, byref(c_replay))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_replay.value)

    def nvmlDeviceGetDriverModel(self, handle):
        c_currModel = _nvmlDriverModel_t()
        c_pendingModel = _nvmlDriverModel_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetDriverModel")
        ret = fn(handle, byref(c_currModel), byref(c_pendingModel))
        self.__nvmlCheckReturn(ret)
        return [c_currModel.value, c_pendingModel.value]

    # added to API
    def nvmlDeviceGetCurrentDriverModel(self, handle):
        return self.nvmlDeviceGetDriverModel(handle)[0]

    # added to API
    def nvmlDeviceGetPendingDriverModel(self, handle):
        return self.nvmlDeviceGetDriverModel(handle)[1]

    # Added in 2.285
    def nvmlDeviceGetVbiosVersion(self, handle):
        c_version = create_string_buffer(NVML_DEVICE_VBIOS_VERSION_BUFFER_SIZE)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetVbiosVersion")
        ret = fn(handle, c_version, c_uint(NVML_DEVICE_VBIOS_VERSION_BUFFER_SIZE))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_version.value)

    # Added in 2.285
    def nvmlDeviceGetComputeRunningProcesses(self, handle):
        # first call to get the size
        c_count = c_uint(0)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetComputeRunningProcesses")
        ret = fn(handle, byref(c_count), None)

        if (ret == NVML_SUCCESS):
            # special case, no running processes
            return []
        elif (ret == NVML_ERROR_INSUFFICIENT_SIZE):
            # typical case
            # oversize the array incase more processes are created
            c_count.value = c_count.value * 2 + 5
            proc_array = c_nvmlProcessInfo_t * c_count.value
            c_procs = proc_array()

            # make the call again
            ret = fn(handle, byref(c_count), c_procs)
            self.__nvmlCheckReturn(ret)

            procs = []
            for i in range(c_count.value):
                # use an alternative struct for this object
                obj = nvmlStructToFriendlyObject(c_procs[i])
                if (obj.usedGpuMemory == NVML_VALUE_NOT_AVAILABLE_ulonglong.value):
                    # special case for WDDM on Windows, see comment above
                    obj.usedGpuMemory = None
                procs.append(obj)

            return procs
        else:
            # error case
            raise NVMLError(ret)

    def nvmlDeviceGetGraphicsRunningProcesses(self, handle):
        # first call to get the size
        c_count = c_uint(0)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetGraphicsRunningProcesses")
        ret = fn(handle, byref(c_count), None)

        if (ret == NVML_SUCCESS):
            # special case, no running processes
            return []
        elif (ret == NVML_ERROR_INSUFFICIENT_SIZE):
            # typical case
            # oversize the array incase more processes are created
            c_count.value = c_count.value * 2 + 5
            proc_array = c_nvmlProcessInfo_t * c_count.value
            c_procs = proc_array()

            # make the call again
            ret = fn(handle, byref(c_count), c_procs)
            self.__nvmlCheckReturn(ret)

            procs = []
            for i in range(c_count.value):
                # use an alternative struct for this object
                obj = nvmlStructToFriendlyObject(c_procs[i])
                if (obj.usedGpuMemory == NVML_VALUE_NOT_AVAILABLE_ulonglong.value):
                    # special case for WDDM on Windows, see comment above
                    obj.usedGpuMemory = None
                procs.append(obj)

            return procs
        else:
            # error case
            raise NVMLError(ret)

    def nvmlDeviceGetAutoBoostedClocksEnabled(self, handle):
        c_isEnabled = _nvmlEnableState_t()
        c_defaultIsEnabled = _nvmlEnableState_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetAutoBoostedClocksEnabled")
        ret = fn(handle, byref(c_isEnabled), byref(c_defaultIsEnabled))
        self.__nvmlCheckReturn(ret)
        return [c_isEnabled.value, c_defaultIsEnabled.value]
        #Throws NVML_ERROR_NOT_SUPPORTED if hardware doesn't support setting auto boosted clocks

    ## Set functions
    def nvmlUnitSetLedState(self, unit, color):
        fn = self.__nvmlGetFunctionPointer("nvmlUnitSetLedState")
        ret = fn(unit, _nvmlLedColor_t(color))
        self.__nvmlCheckReturn(ret)
        return None

    def nvmlDeviceSetPersistenceMode(self, handle, mode):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetPersistenceMode")
        ret = fn(handle, _nvmlEnableState_t(mode))
        self.__nvmlCheckReturn(ret)
        return None

    def nvmlDeviceSetComputeMode(self, handle, mode):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetComputeMode")
        ret = fn(handle, _nvmlComputeMode_t(mode))
        self.__nvmlCheckReturn(ret)
        return None

    def nvmlDeviceSetEccMode(self, handle, mode):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetEccMode")
        ret = fn(handle, _nvmlEnableState_t(mode))
        self.__nvmlCheckReturn(ret)
        return None

    def nvmlDeviceClearEccErrorCounts(self, handle, counterType):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceClearEccErrorCounts")
        ret = fn(handle, _nvmlEccCounterType_t(counterType))
        self.__nvmlCheckReturn(ret)
        return None

    def nvmlDeviceSetDriverModel(self, handle, model):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetDriverModel")
        ret = fn(handle, _nvmlDriverModel_t(model))
        self.__nvmlCheckReturn(ret)
        return None

    def nvmlDeviceSetAutoBoostedClocksEnabled(self, handle, enabled):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetAutoBoostedClocksEnabled")
        ret = fn(handle, _nvmlEnableState_t(enabled))
        self.__nvmlCheckReturn(ret)
        return None
        #Throws NVML_ERROR_NOT_SUPPORTED if hardware doesn't support setting auto boosted clocks

    def nvmlDeviceSetDefaultAutoBoostedClocksEnabled(self, handle, enabled, flags):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetDefaultAutoBoostedClocksEnabled")
        ret = fn(handle, _nvmlEnableState_t(enabled), c_uint(flags))
        self.__nvmlCheckReturn(ret)
        return None
        #Throws NVML_ERROR_NOT_SUPPORTED if hardware doesn't support setting auto boosted clocks

    # Added in 4.304
    def nvmlDeviceSetApplicationsClocks(self, handle, maxMemClockMHz, maxGraphicsClockMHz):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetApplicationsClocks")
        ret = fn(handle, c_uint(maxMemClockMHz), c_uint(maxGraphicsClockMHz))
        self.__nvmlCheckReturn(ret)
        return None

    # Added in 4.304
    def nvmlDeviceResetApplicationsClocks(self, handle):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceResetApplicationsClocks")
        ret = fn(handle)
        self.__nvmlCheckReturn(ret)
        return None

    # Added in 4.304
    def nvmlDeviceSetPowerManagementLimit(self, handle, limit):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetPowerManagementLimit")
        ret = fn(handle, c_uint(limit))
        self.__nvmlCheckReturn(ret)
        return None

    # Added in 4.304
    def nvmlDeviceSetGpuOperationMode(self, handle, mode):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetGpuOperationMode")
        ret = fn(handle, _nvmlGpuOperationMode_t(mode))
        self.__nvmlCheckReturn(ret)
        return None

    # Added in 2.285
    def nvmlEventSetCreate(self):
        fn = self.__nvmlGetFunctionPointer("nvmlEventSetCreate")
        eventSet = c_nvmlEventSet_t()
        ret = fn(byref(eventSet))
        self.__nvmlCheckReturn(ret)
        return eventSet

    # Added in 2.285
    def nvmlDeviceRegisterEvents(self, handle, eventTypes, eventSet):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceRegisterEvents")
        ret = fn(handle, c_ulonglong(eventTypes), eventSet)
        self.__nvmlCheckReturn(ret)
        return None

    # Added in 2.285
    def nvmlDeviceGetSupportedEventTypes(self, handle):
        c_eventTypes = c_ulonglong()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetSupportedEventTypes")
        ret = fn(handle, byref(c_eventTypes))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_eventTypes.value)

    # Added in 2.285
    # raises NVML_ERROR_TIMEOUT exception on timeout
    def nvmlEventSetWait(self, eventSet, timeoutms):
        fn = self.__nvmlGetFunctionPointer("nvmlEventSetWait")
        data = c_nvmlEventData_t()
        ret = fn(eventSet, byref(data), c_uint(timeoutms))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(data)

    # Added in 2.285
    def nvmlEventSetFree(self, eventSet):
        fn = self.__nvmlGetFunctionPointer("nvmlEventSetFree")
        ret = fn(eventSet)
        self.__nvmlCheckReturn(ret)
        return None

    # Added in 3.295
    def nvmlDeviceOnSameBoard(self, handle1, handle2):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceOnSameBoard")
        onSameBoard = c_int()
        ret = fn(handle1, handle2, byref(onSameBoard))
        self.__nvmlCheckReturn(ret)
        return (onSameBoard.value != 0)

    # Added in 3.295
    def nvmlDeviceGetCurrPcieLinkGeneration(self, handle):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetCurrPcieLinkGeneration")
        gen = c_uint()
        ret = fn(handle, byref(gen))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(gen.value)

    # Added in 3.295
    def nvmlDeviceGetMaxPcieLinkGeneration(self, handle):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetMaxPcieLinkGeneration")
        gen = c_uint()
        ret = fn(handle, byref(gen))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(gen.value)

    # Added in 3.295
    def nvmlDeviceGetCurrPcieLinkWidth(self, handle):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetCurrPcieLinkWidth")
        width = c_uint()
        ret = fn(handle, byref(width))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(width.value)

    # Added in 3.295
    def nvmlDeviceGetMaxPcieLinkWidth(self, handle):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetMaxPcieLinkWidth")
        width = c_uint()
        ret = fn(handle, byref(width))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(width.value)

    # Added in 4.304
    def nvmlDeviceGetSupportedClocksThrottleReasons(self, handle):
        c_reasons= c_ulonglong()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetSupportedClocksThrottleReasons")
        ret = fn(handle, byref(c_reasons))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_reasons.value)

    # Added in 4.304
    def nvmlDeviceGetCurrentClocksThrottleReasons(self, handle):
        c_reasons= c_ulonglong()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetCurrentClocksThrottleReasons")
        ret = fn(handle, byref(c_reasons))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_reasons.value)

    # Added in 5.319
    def nvmlDeviceGetIndex(self, handle):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetIndex")
        c_index = c_uint()
        ret = fn(handle, byref(c_index))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_index.value)


    # Added in 5.319
    def nvmlDeviceGetAccountingMode(self, handle):
        c_mode = _nvmlEnableState_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetAccountingMode")
        ret = fn(handle, byref(c_mode))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_mode.value)


    def nvmlDeviceSetAccountingMode(self, handle, mode):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetAccountingMode")
        ret = fn(handle, _nvmlEnableState_t(mode))
        self.__nvmlCheckReturn(ret)
        return None


    def nvmlDeviceClearAccountingPids(self, handle):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceClearAccountingPids")
        ret = fn(handle)
        self.__nvmlCheckReturn(ret)
        return None


    def nvmlDeviceGetAccountingStats(self, handle, pid):
        stats = c_nvmlAccountingStats_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetAccountingStats")
        ret = fn(handle, c_uint(pid), byref(stats))
        self.__nvmlCheckReturn(ret)
        if (stats.maxMemoryUsage == NVML_VALUE_NOT_AVAILABLE_ulonglong.value):
            # special case for WDDM on Windows, see comment above
            stats.maxMemoryUsage = None
        return bytes_to_str(stats)


    def nvmlDeviceGetAccountingPids(self, handle):
        count = c_uint(self.nvmlDeviceGetAccountingBufferSize(handle))
        pids = (c_uint * count.value)()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetAccountingPids")
        ret = fn(handle, byref(count), pids)
        self.__nvmlCheckReturn(ret)
        return list(map(int, pids[0:count.value]))


    def nvmlDeviceGetAccountingBufferSize(self, handle):
        bufferSize = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetAccountingBufferSize")
        ret = fn(handle, byref(bufferSize))
        self.__nvmlCheckReturn(ret)
        return int(bufferSize.value)


    def nvmlDeviceGetRetiredPages(self, device, sourceFilter):
        c_source = _nvmlPageRetirementCause_t(sourceFilter)
        c_count = c_uint(0)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetRetiredPages")

        # First call will get the size
        ret = fn(device, c_source, byref(c_count), None)

        # this should only fail with insufficient size
        if ((ret != NVML_SUCCESS) and
            (ret != NVML_ERROR_INSUFFICIENT_SIZE)):
            raise NVMLError(ret)

        # call again with a buffer
        # oversize the array for the rare cases where additional pages
        # are retired between NVML calls
        c_count.value = c_count.value * 2 + 5
        page_array = c_ulonglong * c_count.value
        c_pages = page_array()
        ret = fn(device, c_source, byref(c_count), c_pages)
        self.__nvmlCheckReturn(ret)
        return list(map(int, c_pages[0:c_count.value]))


    def nvmlDeviceGetRetiredPagesPendingStatus(self, device):
        c_pending = _nvmlEnableState_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetRetiredPagesPendingStatus")
        ret = fn(device, byref(c_pending))
        self.__nvmlCheckReturn(ret)
        return int(c_pending.value)


    def nvmlDeviceGetAPIRestriction(self, device, apiType):
        c_permission = _nvmlEnableState_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetAPIRestriction")
        ret = fn(device, _nvmlRestrictedAPI_t(apiType), byref(c_permission))
        self.__nvmlCheckReturn(ret)
        return int(c_permission.value)


    def nvmlDeviceSetAPIRestriction(self, handle, apiType, isRestricted):
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceSetAPIRestriction")
        ret = fn(handle, _nvmlRestrictedAPI_t(apiType), _nvmlEnableState_t(isRestricted))
        self.__nvmlCheckReturn(ret)
        return None


    def nvmlDeviceGetBridgeChipInfo(self, handle):
        bridgeHierarchy = c_nvmlBridgeChipHierarchy_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetBridgeChipInfo")
        ret = fn(handle, byref(bridgeHierarchy))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(bridgeHierarchy)


    def nvmlDeviceGetSamples(self, device, sampling_type, timeStamp):
        c_sampling_type = _nvmlSamplingType_t(sampling_type)
        c_time_stamp = c_ulonglong(timeStamp)
        c_sample_count = c_uint(0)
        c_sample_value_type = _nvmlValueType_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetSamples")

        ## First Call gets the size
        ret = fn(device, c_sampling_type, c_time_stamp, byref(c_sample_value_type), byref(c_sample_count), None)

        # Stop if this fails
        if (ret != NVML_SUCCESS):
            raise NVMLError(ret)

        sampleArray = c_sample_count.value * c_nvmlSample_t
        c_samples = sampleArray()
        ret = fn(device, c_sampling_type, c_time_stamp,  byref(c_sample_value_type), byref(c_sample_count), c_samples)
        self.__nvmlCheckReturn(ret)
        return (c_sample_value_type.value, c_samples[0:c_sample_count.value])


    def nvmlDeviceGetViolationStatus(self, device, perfPolicyType):
        c_perfPolicy_type = _nvmlPerfPolicyType_t(perfPolicyType)
        c_violTime = c_nvmlViolationTime_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetViolationStatus")

        ## Invoke the method to get violation time
        ret = fn(device, c_perfPolicy_type, byref(c_violTime))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_violTime)


    def nvmlDeviceGetPcieThroughput(self, device, counter):
        c_util = c_uint()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetPcieThroughput")
        ret = fn(device, _nvmlPcieUtilCounter_t(counter), byref(c_util))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_util.value)


    def nvmlSystemGetTopologyGpuSet(self, cpuNumber):
        c_count = c_uint(0)
        fn = self.__nvmlGetFunctionPointer("nvmlSystemGetTopologyGpuSet")

        # First call will get the size
        ret = fn(cpuNumber, byref(c_count), None)

        if ret != NVML_SUCCESS:
            raise NVMLError(ret)
        print(c_count.value)
        # call again with a buffer
        device_array = c_nvmlDevice_t * c_count.value
        c_devices = device_array()
        ret = fn(cpuNumber, byref(c_count), c_devices)
        self.__nvmlCheckReturn(ret)
        return list(c_devices[0:c_count.value])


    def nvmlDeviceGetTopologyNearestGpus(self, device, level):
        c_count = c_uint(0)
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetTopologyNearestGpus")

        # First call will get the size
        ret = fn(device, level, byref(c_count), None)

        if ret != NVML_SUCCESS:
            raise NVMLError(ret)

        # call again with a buffer
        device_array = c_nvmlDevice_t * c_count.value
        c_devices = device_array()
        ret = fn(device, level, byref(c_count), c_devices)
        self.__nvmlCheckReturn(ret)
        return list(c_devices[0:c_count.value])


    def nvmlDeviceGetTopologyCommonAncestor(self, device1, device2):
        c_level = _nvmlGpuTopologyLevel_t()
        fn = self.__nvmlGetFunctionPointer("nvmlDeviceGetTopologyCommonAncestor")
        ret = fn(device1, device2, byref(c_level))
        self.__nvmlCheckReturn(ret)
        return bytes_to_str(c_level.value)
