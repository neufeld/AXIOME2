#!/usr/bin/env python

import xml.dom.minidom as xml
from os import listdir
from os.path import dirname
#import re

#Finds the install directory, from which the res folder can be found
source_dir = dirname(__file__)
    
class AxiomeAnalysis(object):
    def __init__(self, ax_file, master_file, makefile):
        """AxiomeAnalysis: Class that controls loading and activating
        of modules, creation of resulting Makefile, or launching of UI
        """
        if ax_file:
			try:
				self.ax_file = xml.parse(ax_file)
			except:
				print "Error parsing XML file %s" % ax_file
        try:
            self.master_file = xml.parse(master_file)
        except:
            print "Error parsing XML file %s" % master_file
        #**TODO** Replace with a better AxMakefile class
        #self.makefile = open(makefile,"w")
        #File manifest
        self._manifest = {}
        #Load the modules, which also loads all submodules
        self._modules = self.loadModules(self.getWorkflow())
        #Now load the actual modules in the .ax file
        #But only if the ax file was given
        if ax_file:
			self._activated_submodules = self.activateSubmodules()

    def __del__(self):
        self.ax_file.close()
        self.master_file.close()
        self.makefile.close()
    
    def getModuleByName(self, name):
        """Searches through initiated modules and returns module matching
        the given name
        """
        #Go through the modules and get it by its name
        for module in self._modules:
            if module.name == name:
                return module
        print "Module %s not found" % name
        return False
    
    #**TODO** Go into ax file and get Workflow name
    def getWorkflow(self):
        return "Default"
    
    def loadModules(self, workflow_name):
        """Iterates through workflow, loading all modules by the given
        name. Assumes that the module name exists as a folder in the res
        subfolder.
        """
        for workflow in self.master_file.getElementsByTagName("workflow"): 
            if workflow.getAttribute("name") == workflow_name:
            #Load the correct workflow
                module_list = []
                for module in workflow.childNodes:
                    if module.nodeType == xml.Node.ELEMENT_NODE:
                        #Get the attributes
                        args = {}
                        for i in range(0,module.attributes.length):
                            args[module.attributes.item(i).name] = module.attributes.item(i).value
                        module_list.append(AxModule(self, module.nodeName, args))
        return module_list
        
    def activateSubmodules(self):
        """Activates submodules. This means that the submodules listed
        in the .ax file will be called upon, and initiated submodules
        will be used to check if requirements are met, and to build
        the Makefile.
        """
        activated_submodules = []
        for node in self.ax_file.getElementsByTagName("axiome").item(0).childNodes:
            if node.nodeType == xml.Node.ELEMENT_NODE:
                module_name = node.nodeName
                submodule_name = node.getAttribute("method")
                submodule = self.getModuleByName(module_name).getSubmoduleByName(submodule_name)
                args = {}
                #Form a dict out of the arguments supplied
                for i in range(0,node.attributes.length):
                    #method is a special attribute that defines submodule name
                    if node.attributes.item(i).name != "method":
                        args[node.attributes.item(i).name] = node.attributes.item(i).value
                activated_submodules.append(AxActiveSubmodule(submodule, args))

#An active submodule is one that is currently in use
class AxActiveSubmodule(object):
    """Class for the "activated" submodules. Activated means that the
    user has chosen the submodule in their .ax file, and we need to load
    a specific version with the given arguments
    """
    def __init__(self, submodule, args):
        self._args = args
        self._submodule = submodule
        #Check if the requirements of the module are met
        if not self._submodule._input.requirementsMet(args):
            #**TODO**
            print args
            print ":("

class AxModule(object):
    def __init__(self, analysis, module_name, args):
        """Class for initiated modules. Its job is to hold the properties
        of the module and a list of its initiated submodules.
        """
        self.name = module_name
        print "Initiating module %s..." % self.name
        self._analysis = analysis
        #Default properties
        self._value = {"required":False, "multi":False}
        self.updateProperties(args)
        self._submodules = self.loadSubModules()
    
    def updateProperties(self, args):
        for prop in args:
            if prop in ["required", "multi"]:
                if args[prop].lower() in ["true","t"]:
                    self._value[prop] = True
                else:
                    self._value[prop] = False
    
    def getSubmoduleByName(self, name):
        #Go through the submodules and get it by its name
        for submodule in self._submodules:
            if submodule.name == name:
                return submodule
        print "Submodule %s not found in module" % (name, self.name)
        return False
    
    def loadSubModules(self):
        #Go into the module folder and load all of the submodules
        submodule_list = []
        for submodule in listdir(source_dir + "/res/%s/" % self.name):
            #**TODO** Need to check if it is a file and a .xml suffix
            try:
                xml_obj = xml.parse(source_dir + "/res/%s/%s" % (self.name, submodule))
            except:
                print self.name + " " + submodule
            submodule_list.append(AxSubmodule(self, xml_obj))
        return submodule_list
    
class AxSubmodule(object):
    def __init__(self, module, xml_obj):
        self._module = module
        self.name = xml_obj.getElementsByTagName("plugin").item(0).getAttribute("name")
        print "Intiating submodule %s..." % self.name
        #Go through the submodule, creating the AxInput AxProcess and AxVersion objects
        self._input = AxInput(self, xml_obj.getElementsByTagName("input"))
        self._process = AxProcess(self, xml_obj.getElementsByTagName("process"))
        self._version = AxVersion(self, xml_obj.getElementsByTagName("version"))

class AxInput(object):
    def __init__(self, submodule, xml_obj):
        #Give access to the submodule that originates this object
        self._submodule = submodule
        #Structure that stores all pertinent data
        self._values = {}
        #xml_obj is the <input> sections (including <input> tags)
        #There should only be one of these
        #Populate the values from the XML object
        for node in xml_obj.item(0).childNodes:
            if node.nodeType == xml.Node.ELEMENT_NODE:
                #Get all of the information
                data_type = node.nodeName
                name = node.getAttribute("name")
                label = node.getAttribute("label")
                required = node.getAttribute("required")
                if required.lower() in ["true","t"]:
                    required = True
                else:
                    required = False
                default = node.getAttribute("default")
                self._values[name]={"type":data_type, "label":label, "required":required, "default":default}
                #Optional information for int and float types
                if data_type in ["int","float"]:
                    self._values[name]["min"]=node.getAttribute("min")
                    self._values[name]["max"]=node.getAttribute("max")
                #**TODO** Check if label, name required, min/max required if int/float
                
    def requirementsMet(self, args):
        #Get a list of all required arguments
        required = [ k for k in self._values if self._values[k]["required"] ]
        #Complain if a required argument is missing
        for item in required:
            if item not in args:
                print "Error: Required item %s not in definition" % item
                return False
        for item in args:
            if item not in self._values:
                print "Warning: Unused attribute %s" % item
                return False
        return True
        #**TODO** Check data type and make sure it follows requirements
        #ie, files exist, numbers in range
        
    def getValues():
        return self._values
    
class AxProcess(object):
    def __init__(self, submodule, xml_obj):
        #Give access to the submodule that originates this object
        self._submodule = submodule
        #Structure that stores all pertinent data
        self._values = []
        #xml_obj is the <process> sections (including <process> tags)
        #There can be more than one of these
        #Populate the values from the XML object
        for process in xml_obj:
            process_dict = {"input":[],"output":[], "command":{}}
            for node in process.childNodes:
                if node.nodeType == xml.Node.ELEMENT_NODE:
                    if node.nodeName in ["input","output"]:
                        process_dict[node.nodeName].append(node.getAttribute("name"))
                    else:
                        process_dict["command"]["label"] = node.getAttribute("label")
                        process_dict["command"]["cmd"] = node.getAttribute("cmd")
                        process_dict["command"]["format"] = node.getAttribute("format")
                        process_dict["command"]["input"] = node.getAttribute("input")
                        process_dict["command"]["output"] = node.getAttribute("output")
                        process_dict["command"]["variable"] = node.getAttribute("variable")
            self._values.append(process_dict)
            
    def createMakefileString(self):
        pass
    
class AxVersion(object):
    def __init__(self, submodule, xml_obj):
        #Give access to the submodule that originates this object
        self._submodule = submodule
        #Structure that stores all pertinent data
        self._values = {}
        #xml_obj is the <input> sections (including <input> tags)
        #There should only be one of these
        #Populate the values from the XML object
        for node in xml_obj.item(0).childNodes:
            if node.nodeType == xml.Node.ELEMENT_NODE:
                #Get all of the information
                label = node.getAttribute("label")
                cmd = node.getAttribute("cmd")
                self._values[label] = cmd
                
    def createMakefileString(self):
        makefile_string = ""
        for label, cmd in self._values:
            makefile_string += "\t@echo \"%s\"\n\t%s >> versions.log\n"
        return makefile_string

#class AxMakefile(object):
     #def __init__(self, submodule, xml_obj):
         #pass
