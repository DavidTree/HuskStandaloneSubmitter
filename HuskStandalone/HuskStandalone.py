#!/usr/bin/env python3

from System import *
from System.Diagnostics import *
from System.IO import *

import os

from Deadline.Plugins import *
from Deadline.Scripting import *

from pathlib import Path

def GetDeadlinePlugin():
    return HuskStandalone()

def CleanupDeadlinePlugin(deadlinePlugin):
    deadlinePlugin.Cleanup()

class HuskStandalone(DeadlinePlugin):
    # functions inside a class must be indented in python - DT
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable # get the renderExecutable Location
        self.RenderArgumentCallback += self.RenderArgument # get the arguments to go after the EXE

    def Cleanup( self ):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def InitializeProcess( self ):
        self.SingleFramesOnly=True
        self.StdoutHandling=True
        self.PopupHandling=False

        self.AddStdoutHandlerCallback("USD ERROR(.*)").HandleCallback += self.HandleStdoutError # detect this error
        self.AddStdoutHandlerCallback( r"ALF_PROGRESS ([0-9]+(?=%))" ).HandleCallback += self.HandleStdoutProgress

    # get path to the executable
    def RenderExecutable(self):
            return self.GetConfigEntry( "USD_RenderExecutable" )

    # get the settings that go after the filename in the render command, 3Delight only has simple options.
    def RenderArgument( self ):

        # construct fileName
        #this will only support 1 frame per task

        usdFile = self.GetPluginInfoEntry("SceneFile")
        usdFile = RepositoryUtils.CheckPathMapping( usdFile )
        usdFile = usdFile.replace( "\\", "/" )

        usdPaddingLength = FrameUtils.GetPaddingSizeFromFilename( usdFile )

        frameNumber = self.GetStartFrame() # check this 2021 USD

        argument = ""
        argument += usdFile + " "

        argument += "--verbose a{} ".format(self.GetPluginInfoEntry("LogLevel"))  # alfred style output and full verbosity

        argument += "--frame {} ".format(frameNumber)

        argument += "--frame-count 1" + " " #only render 1 frame per task

        #renderer handled in job file.
        outputPath = os.path.dirname(usdFile).split('/')[:-3]
        outputPath.append('render')
        outputPath.append('3D_render')
        outputPath = os.path.abspath(os.path.join(*outputPath))
        filename = Path(usdFile).name
        filename = Path(filename).with_suffix("")
        paddedFrameNumber = StringUtils.ToZeroPaddedString(frameNumber,4)
        argument += "-o {0}/{1}/{1}.{2}.exr".format(outputPath,filename,paddedFrameNumber)

        argument += " --make-output-path" + " "

        self.LogInfo( "Rendering USD file: " + usdFile )
        return argument

    # just incase we want to implement progress at some point
    def HandleStdoutProgress(self):
        self.SetStatusMessage(self.GetRegexMatch(0))
        self.SetProgress(float(self.GetRegexMatch(1)))

    # what to do when an error is detected.
    def HandleStdoutError(self):
        self.FailRender(self.GetRegexMatch(0))
