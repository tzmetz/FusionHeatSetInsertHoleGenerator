# Author-tzmetz
# Description-Creates a hole for heat set inserts
# 
# TODO: add chamfer to outer edge of hole 
# TODO: add parameter inputs for M3 Long 
# TODO: make a group for all features used to create the insert hole 

import adsk.core
import adsk.fusion
import traceback
import math

# Defaults for commandInputs
defaultInsertSize = 'M3 Shorty'
defaultInsertLoc = adsk.core.Point3D.create(0, 0, 0)  # creates a point3D object at the origin
defaultInsertPlane = None
defaultInsertSurf = None

# global set of event handlers to keep them referenced for the duration of the command
handlers = []

# Returns the root Fusion 360 object (e.g. the top of the object model https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/SupportFiles/Fusion.pdf)
app = adsk.core.Application.get()

# Returns the root of the userInterface object model (see the Fusion object model)
if app:
    ui = app.userInterface


class HSICommandExecuteHandler(adsk.core.CommandEventHandler):
    """ Event Handler that runs whenever the "okay" button is pressed or when running a preview of the command when all command inputs have been given"""
    
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            
            command = args.firingEvent.sender # this is adsk.core.CommandEventHandler.firingEvent.sender 
            # .firingEvent is The event that the firing is in response to .sender is a property of an event obj 
            # that returns The object that is firing the event. For example, in the case of a command input event this will return the command.
            
            # Now that we now the command that led to the firing of the event which triggered this handler to execute, lets get its user inputs
            inputs = command.commandInputs

            HSI = HS_Insert()  # Create a new instance of the Heat set insert class 

            # Populate properties of the heat set insert class based on inputs from the command dialogue
            for input in inputs:
                if input.id == 'insertSize':
                    HSI.insertSize = input.selectedItem.name
                elif input.id == 'insertLoc':
                    selection = input.selection(0)  # returns the selected entity which in this case should be a sketchpoint. Returns a sketchPoint obj, will return a Point3D if .point is used
                    HSI.insertLoc = selection.entity
                elif input.id == 'insertPlane':
                    HSI.insertPlane = input.selection(0).entity
                elif input.id == 'insertSurf':
                    HSI.insertSurf = input.selection(0).entity  # returns a BRepFace object
            
            # Run the build method
            HSI.buildHole()
            
            args.isValidResult = True  # Used during the commandStarting event to get or set that the result of preview is valid and the command can reuse the result when Ok is hit. 
            # This property should be ignored for all events besides the executePreview event.

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class HSICommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class HSICommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    """ Event Handler that runs to initialize the command window"""
    
    def __init__(self):
        super().__init__()        
    
    def notify(self, args):
        try:
            # Define Command Object and set some of its properties
            cmd = args.command  # Creates a new commmand obj
            cmd.isRepeatable = True  # Sets command obj property to not allow this cmd to be suggested repeatable in the mouse menu
            
            # -------------- Set up Command Event - Handler Relationships -------------------
            # Setting up the event that is fired when the user hits "okay" on the dialogue
            # connects the handler (BoltCommandExecuteHandler()) to the event cmd.execute
                # cmd.execute returns an event
                # Gets an event that is fired when the command has completed gathering the required input and now needs to perform whatever action the command does.
            onExecute = HSICommandExecuteHandler()
            cmd.execute.add(onExecute)
            
            # Setting up the event that is fired when enough information is gathered to provide a preview of the cmd
            # connects the handler (BoltCommandExecuteHandler()) to the event cmd.executePreview
                # cmd.executePreview returns an event
                # Gets an event that is fired when the command has completed gathering the required input and now needs to perform a preview
            onExecutePreview = HSICommandExecuteHandler()
            cmd.executePreview.add(onExecutePreview)
            
            # Setting up the event that is fired when the cmd is canceled
            # connects the handler (BoltCommandDestroyHandler()) to the event cmd.destroy
                # cmd.destroy returns an event
                # Gets an event that is fired when the command is destroyed. The command is destroyed and can be cleaned up.
            onDestroy = HSICommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            
            # keep the handlers referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onExecutePreview)
            handlers.append(onDestroy)

            # ---------------------- Set up Command Inputs --------------------
            # define the inputs
            inputs = cmd.commandInputs  # Gets the associated CommandInputs object which provides the ability to create new command inputs and
            # provides access to any existing inputs that have already been created for this command.
            # Returns a commandInputs Obj https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-504c1dbc-5132-454e-86fd-72101fa55d84 

            # Create a selectionInput Object to select a sketchpoint
            userSelection = inputs.addSelectionInput('insertLoc', 'Insert Location', 'Select a sketchpoint to place the heat set insert hole')
            userSelection.addSelectionFilter(adsk.core.SelectionCommandInput.SketchPoints) 
            userSelection.setSelectionLimits(1)

            # Create a selectionInput Object to select a surface
            userSelection = inputs.addSelectionInput('insertSurf', 'Insert Surface', 'Select hole top surface')
            userSelection.addSelectionFilter(adsk.core.SelectionCommandInput.SolidFaces) 
            userSelection.setSelectionLimits(1)

            # Create a selectionInput Object to select a plane
            # userSelection = inputs.addSelectionInput('insertPlane', 'Insert Plane', 'Select a plane for insert revolve')
            # userSelection.addSelectionFilter(adsk.core.SelectionCommandInput.ConstructionPlanes) 
            # userSelection.setSelectionLimits(1)
            
            # Create a DropDownCommandInput Object
            dropDwn = inputs.addDropDownCommandInput('insertSize', 'Insert Size', adsk.core.DropDownStyles.TextListDropDownStyle)
            dropDwnItems = dropDwn.listItems
            dropDwnItems.add('M3 Shorty', True, '')
            dropDwnItems.add('M4', False, '')

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class HS_Insert:
    # Setting default properties
    def __init__(self):
        self._insertSize = defaultInsertSize
        self._insertLoc = defaultInsertLoc
        self._insertPlane = defaultInsertPlane
        self._insertSurf = defaultInsertSurf

    # Defining setters for class properties
    @property
    def insertSize(self):
        return self._insertSize
    @insertSize.setter
    def insertSize(self, value):
        self._insertSize = value

    @property
    def insertLoc(self):
        return self._insertLoc
    @insertLoc.setter
    def insertLoc(self, value):
        self._insertLoc = value

    @property
    def insertPlane(self):
        return self._insertPlane
    @insertPlane.setter
    def insertPlane(self, value):
        self._insertPlane = value
    
    @property
    def insertSurf(self):
        return self._insertSurf
    @insertSurf.setter
    def insertSurf(self, value):
        self._insertSurf = value

    def buildHole(self):
        """ Method that programatically models the heat set insert hole. This is the primary function of the entire script"""
        
        # Determine correct parameter set to use 
        if self.insertSize == 'M3 Shorty':
            A = 0.42  # OD of the insert [cm]
            angleVal = 85.0/57.2957795  # Draft angle of the heat set insert hole [rad]
            D = 0.3/math.cos((math.pi/2.0) - angleVal)  # Depth of the heat set insert hole [cm]
            B3 = 0.3  # ID of the relief hole beneath the heat set insert hole [cm]
            B1 = (A/2.0) - (0.3*math.tan((math.pi/2.0) - angleVal)) - (B3/2.0)  # Distance between bottom edge of heat set insert hole and top edge of relief hole [cm]
            B2 = 0.25  # Depth of relief hole [cm]
            
        # Get the active design.
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)

        # Get the active component of the active design
        activeComp = design.activeComponent
        
        # Get component planes
        planes = activeComp.constructionPlanes
        planeInput = planes.createInput()
        xyPlane = activeComp.xYConstructionPlane

        # Get construction axes from active component 
        axes = activeComp.constructionAxes
        axisInput = axes.createInput()      

        # Get sketches from active component
        sketches = activeComp.sketches

        # Create an axis normal to the selected face at the selected point
        axisInput.setByNormalToFaceAtPoint(self.insertSurf, self.insertLoc)
        axis = axes.add(axisInput)

        # Create a plane at a 0deg angle to this new axis 
        angle = adsk.core.ValueInput.createByString('0.0 deg')
        planeInput.setByAngle(axis, angle, xyPlane)
        plane = planes.add(planeInput)
        
        # Create a new sketch on this newly created plane
        sketch = sketches.add(plane)

        # Project selected sketchpoint into this new sketch 
        centerPoint = sketch.project(self.insertLoc)[0]   # Returns an object collection which we index to get the sketchpoint obj

        # Project construction axis into this new sketch
        constructionAxisLine = sketch.project(axis)[0]
        constructionAxisLine.isConstruction = True

        # Create object to handle sketch line creation
        lines = sketch.sketchCurves.sketchLines
        
        # Create object to handle sketch dimensions
        skDims = sketch.sketchDimensions

        # Create Axis Line
        lineAxis = lines.addByTwoPoints(centerPoint, adsk.core.Point3D.create(0, 0, 0))

        # Dimension Axis Line
        skDims.addDistanceDimension(centerPoint, lineAxis.endSketchPoint, 0, adsk.core.Point3D.create(0, 0, 0))
        parameterList = design.allParameters
        lastDim = parameterList.item(parameterList.count-1)
        lastDim.value = D + B2

        # Create Line A
        endPointA = adsk.core.Point3D.create(0, 1, 0)
        lineA = lines.addByTwoPoints(centerPoint, endPointA)
        
        # Cosntrain Line A 
        sketch.geometricConstraints.addPerpendicular(lineAxis, lineA)

        # Create Line A dimension
        skDims.addDistanceDimension(centerPoint, lineA.endSketchPoint, 0, endPointA)
        
        # Set Dimension of Line A
        parameterList = design.allParameters
        lastDim = parameterList.item(parameterList.count-1)
        lastDim.value = A/2.0

        # Create Line D
        endPointD = adsk.core.Point3D.create(1, 0, 0)
        lineD = lines.addByTwoPoints(lineA.endSketchPoint, endPointD)

        # Set length of line D 
        skDims.addDistanceDimension(lineA.endSketchPoint, lineD.endSketchPoint, 0, endPointD)
        parameterList = design.allParameters
        lastDim = parameterList.item(parameterList.count-1)
        lastDim.value = D
        
        # Set angle between line A and line D
        skDims.addAngularDimension(lineA, lineD, endPointD)
        parameterList = design.allParameters
        lastDim = parameterList.item(parameterList.count-1)
        lastDim.value = angleVal

        # Make line B1 
        endPointB1 = adsk.core.Point3D.create(-1, 0, 0)
        lineB1 = lines.addByTwoPoints(lineD.endSketchPoint, endPointB1)
        skDims.addDistanceDimension(lineD.endSketchPoint, lineB1.endSketchPoint, 0, endPointB1)

        # Constrain line B1 
        sketch.geometricConstraints.addParallel(lineA, lineB1)

        # Set sketch dim on line B1 
        parameterList = design.allParameters
        lastDim = parameterList.item(parameterList.count-1)
        lastDim.value = B1

        # Make Line B2 
        endPointB2 = adsk.core.Point3D.create(1, -1, 0)
        lineB2 = lines.addByTwoPoints(lineB1.endSketchPoint, endPointB2)
        skDims.addDistanceDimension(lineB1.endSketchPoint, lineB2.endSketchPoint, 0, endPointB2)

        # Constrain Line B2 
        sketch.geometricConstraints.addPerpendicular(lineB1, lineB2)

        # Set Sketch Dim on Line B2 
        parameterList = design.allParameters
        lastDim = parameterList.item(parameterList.count-1)
        lastDim.value = B2 

        # Make Line B3 
        lineB3 = lines.addByTwoPoints(lineB2.endSketchPoint, lineAxis.endSketchPoint)

        # Get the newly created sketch profile 
        prof = sketch.profiles.item(0)

        # Create Revolve Feature
        revolves = activeComp.features.revolveFeatures
        revolveInput = revolves.createInput(prof, axis, adsk.fusion.FeatureOperations.CutFeatureOperation)
        angle = adsk.core.ValueInput.createByReal(2.0*math.pi)  # for some reason I get a tool body creation error if angle extent is not specified
        revolveInput.setAngleExtent(False, angle)
        revolveFeature = revolves.add(revolveInput)
      

def run(context):
    """ Start here: this is the main function of the script """
    
    try:
        # Check to make sure the user is in the "Model" Workspace
        product = app.activeProduct # Returns a product object which is the base class for Fusion 360 i.e. a design object https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-c1fb15c9-0117-4666-a8c3-2dd305f7f6ac
        design = adsk.fusion.Design.cast(product) # Not sure what this is doing seems like its just casting .Desing (design obj) to product (another design obj?) 
        if not design:
            ui.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.') # ui is a global var
            return
        
        commandDefinitions = ui.commandDefinitions # returns collection obj that Provides access to all of the available command definitions. 
        # This is all those created via the API but also includes the command definitions defined by Fusion 360 for the native commands.

        # check the command exists or not
        cmdDef = commandDefinitions.itemById('HS_Insert') # returns a commandDefinition object (note this is different from a commandDefinitions Obj)
        if not cmdDef:
            # Creates a new command definition that can be used to create a button control and handle the response when the button is clicked.
            # See description of parameters here https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-04eb6198-72cd-4430-a6a4-8d68a1105b8e
            cmdDef = commandDefinitions.addButtonDefinition('HS_Insert',
                    'Create Heat Set Insert Feature',
                    'Create hole for heat set insert',
                    './resources') # relative resource file path is specified. This is a folder containing the .png files for displaying the button

        # Setting up the initial event that is fired when the script is ran from Fusion
        # connects the handler (BoltCommandCreatedHandler()) to the event cmdDef.commandCreated
            # cmdDef.commandCreated returns an event
            # This event is fired when the associated control (cmdDef) is manipulated by the user (i.e. running the script). A new Command object is created and passed back through this event 
            # which you can then use to interact with the user to get any input the command requires.
        onCommandCreated = HSICommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)

        inputs = adsk.core.NamedValues.create() # Creates a transient NamedValues object.
        cmdDef.execute(inputs) # Executes this command definition. This is the same as the user clicking a button that is associated with this command definition.
            # returns boolean true if successful execution 
            # optional input: A list of named values that will provide input to the command. The values supported are unique for each command. and not all commands support input values. 


        # prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire. We are waiting for the user to create an event
        adsk.autoTerminate(False)
   
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
