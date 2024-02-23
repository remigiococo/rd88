# Real-time MIDI playback in Win32
# No extra dlls or modules needed, uses built-in ctypes module.
# By Ben Fisher, 2009, GPLv3
# referencing code:
#   http://www.sabren.net/rants/2000/01/20000129a.php3  (uses out-of-date libraries)
#   http://msdn.microsoft.com/en-us/library/ms711632.aspx
# Note: will raise Win32MidiException if no midi device is found, and under other cases!
# Must call .openDevice() before use!
# Remember to call .closeDevice() when done.


import sys
if sys.platform != 'win32':
    raise RuntimeError('Intended for use on win32 platform')
import time
#import exceptions
import ctypes
from ctypes import windll, c_buffer, c_void_p, c_int, byref, sizeof, c_char_p
from ctypes.wintypes import *

class MIDIINCAPS(ctypes.Structure):

    _fields_ = [
        ('wMid', WORD),
        ('wPid', WORD),
        ('vDriverVersion', UINT),
        ('szPname', BYTE * 64),
        ('dwSupport', DWORD),
    ]
    
class MIDIOUTCAPS(ctypes.Structure):

    _fields_ = [

        ('wMid', WORD),
        ('wPid', WORD),
        ('vDriverVersion', UINT),
        ('szPname', BYTE * 64),
        ('wTechnology', WORD),
        ('wVoices', WORD),
        ('wNotes', WORD),
        ('wChannel_mask', WORD),
        ('dwSupport', DWORD),
    ]
    
    device_type = [

        'NONE',
        'MOD_MIDIPORT',     # MIDI hardware port.
        'MOD_SYNTH',        # Synthesizer.
        'MOD_SQSYNTH',      # Square wave synthesizer.
        'MOD_FMSYNTH',      # FM synthesizer
        'MOD_MAPPER',       # Microsoft MIDI mapper.
        'MOD_WAVETABLE',    # Hardware wavetable synthesizer.
        'MOD_SWSYNTH',      # Software synthesizer.
        'NONE',
    ]

'''
typedef struct midihdr_tag {
  LPSTR              lpData;
  DWORD              dwBufferLength;
  DWORD              dwBytesRecorded;
  DWORD_PTR          dwUser;
  DWORD              dwFlags;
  struct midihdr_tag  *lpNext;
  DWORD_PTR          reserved;
  DWORD              dwOffset;
  DWORD_PTR          dwReserved[4];
} MIDIHDR, *LPMIDIHDR;
'''
class MIDIHDR(ctypes.Structure):

  _fields_ = [
  
    ('lpData', LPSTR),
    ('dwBufferLength', DWORD),
    ('dwBytesRecorded', DWORD),
    ('dwUser', PDWORD),
    ('dwFlags', DWORD),
    ('lpNext', LPCVOID), # ???
    ('reserved', PDWORD),
    ('dwOffset', DWORD),
    ('dwReserved', PDWORD * 4)
  ]       
    
class Win32MidiException(Exception): pass

class Win32MidiPlayer():
    
    def __init__(self):
        self.midiOutOpenErrorCodes= {
            (64+4) : 'MIDIERR_NODEVICE  No MIDI port was found. This error occurs only when the mapper is opened.',
            (0+4): 'MMSYSERR_ALLOCATED  The specified resource is already allocated.',
            (0+2): 'MMSYSERR_BADDEVICEID    The specified device identifier is out of range.',
            (0+11): 'MMSYSERR_INVALPARAM    The specified pointer or structure is invalid.',
            (0+7): 'MMSYSERR_NOMEM  The system is unable to allocate or lock memory.', }
        self.midiOutShortErrorCodes={
            (64+6):'MIDIERR_BADOPENMODE     The application sent a message without a status byte to a stream handle.',
            (64+3):'MIDIERR_NOTREADY    The hardware is busy with other data.',
            (0+5):'MMSYSERR_INVALHANDLE     The specified device handle is invalid.',}
        self.winmm = windll.winmm
        
    def countDevices(self):
        return self.winmm.midiOutGetNumDevs()
        
    def listDevices(self):
      ndevs = self.winmm.midiOutGetNumDevs()
      for i in range(ndevs):
        caps = MIDIOUTCAPS()
        #print("caps_size", sizeof(caps)) # debug
        self.winmm.midiOutGetDevCapsA(i, byref(caps), sizeof(caps))
        name = ctypes.string_at(ctypes.cast(caps.szPname, c_char_p)).decode(encoding="utf-8")
        print("Device #", i, " ", name)
        
    def openDevice(self, deviceNumber=-1): #device -1 refers to the default set in midi mapper, usually a good choice
        #it took me some experimentation to get this to work...
        self.hmidi =  c_void_p()
        rc = self.winmm.midiOutOpen(byref(self.hmidi), deviceNumber, 0, 0, 0)
        if rc!=0:
            raise Win32MidiException( 'Error opening device, '+self.midiOutOpenErrorCodes.get(rc,'Unknown error.'))
    def closeDevice(self):
        rc = self.winmm.midiOutClose(self.hmidi)
        if rc!=0:
            raise Win32MidiException('Error closing device')
    def sendNote(self, pitch, duration=1.0, channel=1, volume=60): #duration in seconds
        midimsg = 0x90 + ((pitch) * 0x100) + (volume * 0x10000) + channel
        mm = c_int(midimsg)
        rc = self.winmm.midiOutShortMsg (self.hmidi, mm)
        if rc!=0:
            raise Win32MidiException( 'Error opening device, '+self.midiOutShortErrorCodes.get(rc,'Unknown error.'))
        
        time.sleep(duration)
        
        # turn it off
        midimsg = 0x80 + ((pitch) * 0x100) + channel
        mm = c_int(midimsg)
        rc = self.winmm.midiOutShortMsg (self.hmidi, mm)
        if rc!=0:
            raise Win32MidiException( 'Error sending event, '+self.midiOutShortErrorCodes.get(rc,'Unknown error.'))

    def rawNoteOn(self, pitch,  channel=1, v=60):
        midimsg = 0x90 + ((pitch) * 0x100) + (v * 0x10000) + channel
        mm = c_int(midimsg)
        rc = self.winmm.midiOutShortMsg (self.hmidi, mm)
        if rc!=0:
            raise Win32MidiException( 'Error sending event, '+self.midiOutShortErrorCodes.get(rc,'Unknown error.'))
            
    def rawNoteOff(self, pitch,  channel=1):
        midimsg = 0x80 + ((pitch) * 0x100) + channel
        mm = c_int(midimsg)
        rc = self.winmm.midiOutShortMsg (self.hmidi, mm)
        if rc!=0:
            raise Win32MidiException( 'Error sending event, '+self.midiOutShortErrorCodes.get(rc,'Unknown error.'))
    
    def programChange(self, program,  channel=1):
        p = program
        v = 0
        midimsg = 0xC0 + ((p) * 0x100) + (v * 0x10000) + channel
        mm = c_int(midimsg)
        rc = self.winmm.midiOutShortMsg (self.hmidi, mm)
        if rc!=0:
            raise Win32MidiException( 'Error sending event, '+self.midiOutShortErrorCodes.get(rc,'Unknown error.'))
            
    def controllerChange(self, controller, val, channel=1):
        midimsg = 0xB0 + ((controller) * 0x100) + (val * 0x10000) + channel
        mm = c_int(midimsg)
        rc = self.winmm.midiOutShortMsg (self.hmidi, mm)
        if rc!=0:
            raise Win32MidiException( 'Error sending event, '+self.midiOutShortErrorCodes.get(rc,'Unknown error.'))
        
class Win32MidiIO():
  def __init__(self):
    self.midiOutOpenErrorCodes= {
        (64+4) : 'MIDIERR_NODEVICE  No MIDI port was found. This error occurs only when the mapper is opened.',
        (0+4): 'MMSYSERR_ALLOCATED  The specified resource is already allocated.',
        (0+2): 'MMSYSERR_BADDEVICEID    The specified device identifier is out of range.',
        (0+11): 'MMSYSERR_INVALPARAM    The specified pointer or structure is invalid.',
        (0+7): 'MMSYSERR_NOMEM  The system is unable to allocate or lock memory.', }
    self.midiOutShortErrorCodes={
        (64+6):'MIDIERR_BADOPENMODE     The application sent a message without a status byte to a stream handle.',
        (64+3):'MIDIERR_NOTREADY    The hardware is busy with other data.',
        (0+5):'MMSYSERR_INVALHANDLE     The specified device handle is invalid.',}
    self.winmm = windll.winmm
    self.listIn = []
    self.listOut = []
    self.debug = False
    
  def numInputDevices(self):
    return self.winmm.midiInGetNumDevs()
    
  def listInputDevices(self):
    ndevs = self.winmm.midiInGetNumDevs()
    if self.debug:
      print("n. of Midi Input devices:", ndevs) # debug
    for i in range(ndevs):
      caps = MIDIINCAPS()
      #print("caps_size", sizeof(caps)) # debug
      self.winmm.midiInGetDevCapsA(i, byref(caps), sizeof(caps))
      name = ctypes.string_at(ctypes.cast(caps.szPname, c_char_p)).decode(encoding="utf-8")
      if name not in self.listIn:
        self.listIn.append(name)
      if self.debug:  
        print("Input Device #", i, " ", name)

  def numOutputDevices(self):
    return self.winmm.midiOutGetNumDevs()
    
  def listOutputDevices(self):
    ndevs = self.winmm.midiOutGetNumDevs()
    if self.debug:
      print("n. of Midi Output devices:", ndevs) # debug
    for i in range(ndevs):
      caps = MIDIOUTCAPS()
      #print("caps_size", sizeof(caps)) # debug
      self.winmm.midiOutGetDevCapsA(i, byref(caps), sizeof(caps))
      name = ctypes.string_at(ctypes.cast(caps.szPname, c_char_p)).decode(encoding="utf-8")
      if name not in self.listOut:
        self.listOut.append(name)
      if self.debug:  
        print("Output Device #", i, " ", name)

  def openOutputDevice(self, deviceNumber=-1): #device -1 refers to the default set in midi mapper, usually a good choice
      #it took me some experimentation to get this to work...
      self.hmidi_o =  c_void_p()
      rc = self.winmm.midiOutOpen(byref(self.hmidi_o), deviceNumber, 0, 0, 0)
      if rc!=0:
          raise Win32MidiException( 'Error opening device, '+self.midiOutOpenErrorCodes.get(rc,'Unknown error.'))
          
  def closeOutputDevice(self):
    if self.hmidi_o == None:
      return
    rc = self.winmm.midiOutClose(self.hmidi_o)
    if rc!=0:
        raise Win32MidiException('Error closing device')

  def openInputDevice(self, deviceNumber=-1): #device -1 refers to the default set in midi mapper, usually a good choice
      self.hmidi_i =  c_void_p()
      rc = self.winmm.midiInOpen(byref(self.hmidi_i), deviceNumber, 0, 0, 0)
      if rc!=0:
          raise Win32MidiException( 'Error opening device, '+self.midiOutOpenErrorCodes.get(rc,'Unknown error.'))
          
  def closeInputDevice(self):
    if self.hmidi_i == None:
      return
    rc = self.winmm.midiInClose(self.hmidi_i)
    if rc!=0:
      raise Win32MidiException('Error closing device')

  def sendLongMsg(self, data):
    ld = len(data)
    mh = MIDIHDR()
    #byte_array = ctypes.c_ubyte *  ld 
    byte_array = ctypes.create_string_buffer(ld)
    for i in range(ld):
      byte_array[i] = data[i]
      if self.debug:
        print("byte_array", byte_array[i])  
    mh.lpData = ctypes.cast(byte_array, LPSTR)
    #print(mh.lpData)
    mh.dwBufferLength = ld
    mh.dwBytesRecorded = 0
    mh.dwUser = ctypes.cast(0, PDWORD)
    mh.dwFlags = 0
    mh.dwOffset = 0
    mh.dwReserved[0] = mh.dwReserved[1] = mh.dwReserved[2] = mh.dwReserved[3] = ctypes.cast(0, PDWORD)
    mh.reserved = ctypes.cast(0, PDWORD)
    mh.lpNext = ctypes.cast(0, LPCVOID)
    rc = self.winmm.midiOutPrepareHeader(self.hmidi_o, byref(mh), ctypes.sizeof(mh))
    if self.debug:
      print(mh.lpData, mh.dwBufferLength, mh.dwFlags) # debug
    if rc!=0:
      raise Win32MidiException( 'Error preparing long msg, '+self.midiOutOpenErrorCodes.get(rc,'Unknown error.'))
    rc = self.winmm.midiOutLongMsg(self.hmidi_o, byref(mh), ctypes.sizeof(mh))
    if self.debug:
      print(mh.lpData, mh.dwBufferLength, mh.dwFlags) # debug
    if rc!=0:
      raise Win32MidiException( 'Error sending long msg, '+self.midiOutOpenErrorCodes.get(rc,'Unknown error.'))
