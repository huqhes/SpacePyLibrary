#!/usr/bin/env python
#******************************************************************************
# (C) 2014, Stefan Korner, Austria                                            *
#                                                                             *
# The Space Python Library is free software; you can redistribute it and/or   *
# modify it under the terms of the GNU Lesser General Public License as       *
# published by the Free Software Foundation; either version 2.1 of the        *
# License, or (at your option) any later version.                             *
#                                                                             *
# The Space Python Library is distributed in the hope that it will be useful, *
# but WITHOUT ANY WARRANTY; without even the implied warranty of              *
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser     *
# General Public License for more details.                                    *
#******************************************************************************
# Unit Tests                                                                  *
#******************************************************************************
import sys
from UTIL.SYS import Error, LOG, LOG_INFO, LOG_WARNING, LOG_ERROR
import UTIL.SYS, UTIL.TASK, UTIL.TCP

#############
# constants #
#############
LINEBUFFERLEN = 256

###########
# classes #
###########
# =============================================================================
class TCPserver(UTIL.TCP.SingleClientReceivingServer):
  """Subclass of UTIL.TCP.SingleClientReceivingServer"""
  # ---------------------------------------------------------------------------
  def __init__(self, portNr):
    """Initialise attributes only"""
    modelTask = UTIL.TASK.s_processingTask
    UTIL.TCP.SingleClientReceivingServer.__init__(self, modelTask, portNr)
    self.tcpLineBuffer = ""
  # ---------------------------------------------------------------------------
  def receiveCallback(self, socket, stateMask):
    """Callback when a client has send data"""
    LOG("*** receiveCallback ***")
    # read the next set of byte from the data socket
    tcpLineBuffer = self.tcpLineBuffer
    try:
      tcpLineBuffer += self.dataSocket.recv(LINEBUFFERLEN);
      LOG("tcpLineBuffer: " + tcpLineBuffer)
    except Exception, ex:
      # read failed
      LOG_ERROR("Read failed: " + str(ex))
      self.disconnectClient()
      return
    # handle the input: extract the lines from the line buffer
    lines = tcpLineBuffer.split("\n")
    # the last line has to be handled in a special way and can not be
    # processed directly
    lastLine = lines[-1]
    lines = lines[:-1]
    if lastLine == "":
      # read of the data was complete (incl. "\n")
      pass
    else:
      # last line was cutt off and the rest should come with the next read
      self.tcpLineBuffer = lastLine
    for line in lines:
      # remove a terminating "\r" for clients like telnet
      if line[-1] == "\r":
        line = line[:-1]
      # terminate the client connection if exit has been entered (case insensitive)
      upperLine = line.upper()
      if (upperLine == "X") or (upperLine == "EXIT"):
        LOG("Exit requested")
        # send the OK response back to the client
        retString = "OK\n"
        try:
          self.dataSocket.send(retString)
        except Exception, ex:
          LOG_ERROR("Send of OK response failed: " + str(ex))
        # terminate the client connection
        self.disconnectClient();
        return
      if (upperLine == "Q") or (upperLine == "QUIT"):
        LOG("Quit requested")
        # send the OK response back to the client
        retString = "OK\n"
        try:
          self.dataSocket.send(retString)
        except Exception, ex:
          LOG_ERROR("Send of OK response failed: " + str(ex))
        # terminate the client connection
        self.disconnectClient();
        sys.exit(0)
      # delegate the input
      pstatus = self.processLine(line);
      if pstatus == 0:
        LOG("OK")
        # send the OK response back to the TECO
        retString = "OK\n";
        try:
          self.dataSocket.send(retString)
        except Exception, ex:
          LOG_ERROR("Send of OK response failed: " + str(ex))
      else:
        LOG_ERROR(str(pstatus))
        # set the Error response back to the client:
        retString = "Error: execution failed (see log)!\n"
        try:
          self.dataSocket.send(retString)
        except Exception, ex:
          LOG_ERROR("Send of Error response failed: " + str(ex))
  # ---------------------------------------------------------------------------
  def processLine(self, line):
    """Callback when a client has send a data line"""
    LOG("line = " + line)
    return 0

#############
# functions #
#############
# -----------------------------------------------------------------------------
def initConfiguration():
  """initialise the system configuration"""
  UTIL.SYS.s_configuration.setDefaults([
    ["HOST", "192.168.1.100"],
    ["SERVER_PORT", "1234"]])
# -----------------------------------------------------------------------------
def createServer():
  """create the TCP server"""
  server = TCPserver(portNr=int(UTIL.SYS.s_configuration.SERVER_PORT))
  if not server.openConnectPort(UTIL.SYS.s_configuration.HOST):
    sys.exit(-1)
  # activate zyclic idle function
  idleFunction()
# -----------------------------------------------------------------------------
def idleFunction():
  UTIL.TASK.s_processingTask.createTimeHandler(1000, idleFunction)
  LOG("--- idle ---")

########
# main #
########
if __name__ == "__main__":
  # initialise the system configuration
  initConfiguration()
  # initialise the console handler
  consoleHandler = UTIL.TASK.ConsoleHandler()
  # initialise the model
  modelTask = UTIL.TASK.ProcessingTask(isParent=True)
  # register the console handler
  modelTask.registerConsoleHandler(consoleHandler)
  # create the TCP server
  LOG("Open the TCP server")
  createServer()
  # start the tasks
  LOG("start modelTask...")
  modelTask.start()
