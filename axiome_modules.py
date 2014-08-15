#!/usr/bin/env python

import xml.dom.minidom as xml
from os import listdir, mkdir
from os.path import dirname, isfile, splitext, isdir, abspath
import re

#Finds the install directory, from which the res folder can be found
source_dir = dirname(abspath(__file__))

def getWorkflowList():
    master_file = xml.parse(source_dir+"/res/modules/master.xml")
    workflow_list = list()
    for workflow in master_file.getElementsByTagName("workflow"): 
        workflow_list.append(workflow.getAttribute("name"))
    return workflow_list

class AxiomeAnalysis(object):
    def __init__(self, ax_file, workflow = None):
        """AxiomeAnalysis: Class that controls loading and activating
        of modules, creation of resulting Makefile and report
        """
        #An AxAnalysis can be initiated with or without an AXIOME file
        #Without an AXIOME file, we just load all of the plugins
        #This is good for tests, and generating the UI
        if ax_file:
            try:
                self.ax_file = xml.parse(ax_file)
            except:
                raise StandardError, "Error parsing XML file %s" % ax_file
            #Set the working directory to the .ax file location
            #but add axiome as the extension
            self.working_directory = splitext(ax_file)[0] + ".axiome"
            try:
                if not isdir(self.working_directory):
                    mkdir(self.working_directory)
            except OSError:
                raise OSError, "Error: Could not create axiome directory"
            self.makefile = AxMakefile(self.working_directory+"/Makefile")
        else:
            self.working_directory = ""
            self.ax_file = None
        try:
            self.master_file = xml.parse(source_dir+"/res/modules/master.xml")
        except:
            raise StandardError, "Error parsing XML file %s" % master_file
        #File manifest
        #Contains the filenames, and the module and active submodule that owns it
        self._manifest = {}
        #Load the modules, which also loads all submodules
        if workflow:
            self.workflow = workflow
            self._modules = self.loadModules(self.workflow)
        else:
            self.workflow = self.getWorkflow()
            self._modules = self.loadModules(self.workflow)
        #Now load the actual modules in the .ax file
        #But only if the ax file was given
        if ax_file:
            self.report = AxReport(self.working_directory+"/report.html")
            self._activated_submodules = self.activateSubmodules()
            for active_submodule in self._activated_submodules:
                active_submodule._submodule._process.createMakefileString(active_submodule)
            self.report.writeHTML()
            self.makefile.writeMakefile()

    def getModuleByName(self, name):
        """Searches through initiated modules and returns module matching
        the given name
        """
        #Go through the modules and get it by its name
        for module in self._modules:
            if module.name == name:
                return module
        raise ValueError, "Module %s not found" % name
    
    def getWorkflow(self):
        if self.ax_file:
            workflow_list = getWorkflowList()
            workflow = self.ax_file.getElementsByTagName("axiome")[0].getAttribute("workflow")
            if workflow not in workflow_list:
                raise ValueError, "Workflow in loaded .ax file not found in master.xml"
            else:
                return workflow
        else:
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
        return activated_submodules
        
    def getActiveSubmodulesByModuleName(self, name):
        active_submodule_list = list()
        for submodule in self._activated_submodules:
            if submodule._submodule._module.name == name:
                active_submodule_list.append(submodule)
        if not active_submodule_list:
            raise ValueError, "No activated submodules from module '%s' found." % name
        return active_submodule_list
                
    def getActiveSubmodulesBySubmoduleName(self, module_name, submodule_name):
        active_submodule_list = list()
        for submodule in self._activated_submodules:
            if (submodule._submodule.name == submodule_name) & (submodule._submodule._module.name == module_name):
                active_submodule_list.append(submodule)
        if not active_submodule_list:
            raise ValueError, "No activated submodules from submodule '%s' found." % name
        return active_submodule_list

    def getAxFileComments(self):
        comment_list = list()
        for node in self.ax_file.getElementsByTagName("axiome").item(0).childNodes:
            if node.nodeType == xml.Node.COMMENT_NODE:
                comment_list.append(node.data)
        return comment_list


class AxMakefile(object):
    def __init__(self, makefile):
        self._file = open(makefile, "w")
        #Start with a sha-bang declaration
        #**TODO** More informative preamble (date, AXIOME2 version, etc)
        #Build up this file process by process
        self.headerString = "#!/usr/bin/make -f\n#Generated by AXIOME2\n\n"
        #Tabula rasa
        self.makefileString = ""
        #"all" string is a phony file that will allow us to simply run "make"
        #to create everything
        self.allString = "all:"
        
    def __del__(self):
        self._file.close()

    def addProcess(self, input_file_list, output_file_list, command_string):
        #Add the input/output requirements
        self.makefileString += "\n\n" + " ".join(output_file_list) + ": " + " ".join(input_file_list)
        #Add the command string
        self.makefileString += "\n" + command_string
        #Add to the phony all string
        for output_file in output_file_list:
            self.allString += " " + output_file
        
    def writeMakefile(self):
        self._file.write(self.headerString + self.allString + self.makefileString + "\n\n" + ".PHONY: all")
        
#Class which generates the output report file for AXIOME
#For now, this is going to be a simple html file
class AxReport(object):
    def __init__(self, html_file):
        #Store the page as an html string
        self.html_editing = True
        self.html_file = html_file
        self.html_string = "<!DOCTYPE HTML>\n<html>\n<head>\n"
        self.html_string += "<title>AXIOME2 Analysis Results Table of Contents</title>\n"
        self.html_string += "</head>\n<body>\n<h1>Table of Contents</h1>\n"
        self.html_string += "<h4>File links are not active until AXIOME run is complete</h4>\n<ul>\n"
        
    def addToReport(self, label, location):
        self.html_string += "<li><a href=\"" + location + "\">" + label + "</a></li>\n"
        
    def writeHTML(self):
        #Close the HTML document
        self.html_string += "</ul>\n</body>\n</html>"
        self.html_editing = False
        with open(self.html_file, 'w') as html_out:
            html_out.write(self.html_string)


#An active submodule is one that is currently in use
class AxActiveSubmodule(object):
    """Class for the "activated" submodules. Activated means that the
    user has chosen the submodule in their .ax file, and we need to load
    a specific version with the given arguments
    """
    def __init__(self, submodule, args):
        self._submodule = submodule
        #Set the arguments by filling in the defaults, where possible
        self._args = self.fillDefaults(args, submodule)
        #Set a designation for the submodule, for use in making directories
        self.name = self._submodule._module.name + "/" +self._submodule.name
        if self._submodule._module._value["multi"]:
            self.name += str(self._submodule.num_loaded)
            self._submodule.num_loaded += 1
        #Check if the requirements of the module are met
        if not self._submodule._input.requirementsMet(args):
            raise ValueError, "Requirements for submodule '%s', module '%s' not met. Exiting." % (self._submodule.name, self._submodule._module.name)
            
    def fillDefaults(self, args, submodule):
        #Go into the requirements for the submodule
        input_values = self._submodule._input._values
        for item in input_values:
            if item["name"] not in args.keys():
                #If a default exists for it, use it
                if "default" in input_values:
                    args[item]=input_values[item]["default"]
        return args

class AxModule(object):
    def __init__(self, analysis, module_name, args):
        """Class for initiated modules. Its job is to hold the properties
        of the module and a list of its initiated submodules.
        """
        self.name = module_name
        self._analysis = analysis
        #Default properties
        self._value = {"required":False, "multi":False, "label":self.name, "default":list(), "help":""}
        self.updateProperties(args)
        self._submodules = self.loadSubModules()
    
    def updateProperties(self, args):
        for prop in args:
            if prop in ["required", "multi"]:
                if args[prop].lower() in ["true","t"]:
                    self._value[prop] = True
                else:
                    self._value[prop] = False
            elif prop in ["label"]:
                self._value["label"] = args["label"]
            elif prop in ["default"]:
                self._value["default"] = args["default"].replace(" ","").split(",")
            elif prop in ["help"]:
                self._value["help"] = args["help"]
    
    def getSubmoduleByName(self, name):
        #Go through the submodules and get it by its name
        for submodule in self._submodules:
            if submodule.name == name:
                return submodule
        raise ValueError, "Submodule %s not found in module" % (name, self.name)
    
    def loadSubModules(self):
        #Go into the module folder and load all of the submodules
        submodule_list = []
        for submodule in listdir(source_dir + "/res/modules/%s/" % self.name):
            #**TODO** Need to check if it is a file and a .xml suffix
            try:
                xml_obj = xml.parse(source_dir + "/res/modules/%s/%s" % (self.name, submodule))
            except:
                raise StandardError, "Could not parse file '" + source_dir + "/res/modules/%s/%s'" % (self.name, submodule)
            submodule_list.append(AxSubmodule(self, xml_obj))
        return submodule_list
    
class AxSubmodule(object):
    def __init__(self, module, xml_obj):
        self._module = module
        self.name = xml_obj.getElementsByTagName("plugin").item(0).getAttribute("name")
        #Go through the submodule, creating the AxInput AxProcess and AxInfo objects
        self._input = AxInput(self, xml_obj.getElementsByTagName("input"))
        self._process = AxProcess(self, xml_obj.getElementsByTagName("process"))
        self._info = AxInfo(self, xml_obj.getElementsByTagName("info"))
        self.num_loaded = 0

class AxInput(object):
    def __init__(self, submodule, xml_obj):
        #Give access to the submodule that originates this object
        self._submodule = submodule
        #Structure that stores all pertinent data
        self._values = list()
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
                value_dict = {"name":name, "type":data_type, "label":label, "required":required, "default":default}
                #Optional information for int and float types
                if data_type in ["int","float"]:
                    minimum = node.getAttribute("min")
                    maximum = node.getAttribute("max")
                    if not default:
                        if float(minimum) > 0:
                            default = minimum
                        else:
                            default = "0"
                    value_dict["min"]=minimum
                    value_dict["max"]=maximum
                self._values.append(value_dict)
                #**TODO** Check if label, name required, min/max required if int/float
                
    def requirementsMet(self, args):
        #Get a list of all required arguments
        required = [ d["name"] for d in self._values if d["required"] ]
        names = [ d["name"] for d in self._values ]
        #Complain if a required argument is missing
        for item in required:
            if item not in args:
                print "Error: Required item %s not in definition" % item
                return False
        for item in args:
            if (item not in names) & (item != "axiome_submodule"):
                print "Warning: Unused attribute %s" % item
                return False
        return True
        #**TODO** Check data type and make sure it follows requirements
        #ie, files exist, numbers in range
        
    def getValuesForInput(self, name):
        for value_dict in self._values:
            if value_dict["name"] == name:
                return value_dict
        raise ValueError, "Failed to find input name '%s' in submodule '%s'" % (name, self._submodule.name)
    
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
            process_dict = {"input":[],"output":{}, "command":{}}
            for node in process.childNodes:
                if node.nodeType == xml.Node.ELEMENT_NODE:
                    if node.nodeName == "input":
                        process_dict["input"].append(node.getAttribute("name"))
                    elif node.nodeName == "output":
                        process_dict["output"][node.getAttribute("name")] = {}
                        process_dict["output"][node.getAttribute("name")]["report_label"] = node.getAttribute("report_label")
                        process_dict["output"][node.getAttribute("name")]["report_variable"] = node.getAttribute("report_variable")
                    else:
                        process_dict["command"]["label"] = node.getAttribute("label")
                        process_dict["command"]["cmd"] = node.getAttribute("cmd")
                        process_dict["command"]["format"] = node.getAttribute("format")
                        process_dict["command"]["input"] = node.getAttribute("input")
                        process_dict["command"]["output"] = node.getAttribute("output")
                        process_dict["command"]["variable"] = node.getAttribute("variable")
            self._values.append(process_dict)

    def createMakefileString(self, active_submodule):
        #Steps:
        # For each process:
        # - make input/output string
        # - make command string
        for process in self._values:
            input_file_list = list()
            for input_file in process["input"]:
                #Check for variables
                resolved_input_file_list = self.resolve_variable(input_file, active_submodule)
                #Now we need to check if the file exists
                for resolved_input_file in resolved_input_file_list:
                    if not isfile(resolved_input_file):
                        #If it does not, see if it exists in the file manifest
                        if resolved_input_file not in self._submodule._module._analysis._manifest:
                            #If it does not exist in the manifest or on system, complain
                            raise ValueError, "Required input file '%s' called by submodule '%s' does not exist on system and not created by previously called module." % (input_file, active_submodule.name)
                        else:
                            input_file_list.append(self._submodule._module._analysis._manifest[resolved_input_file] + "/" + resolved_input_file)
                    else:
                        input_file_list.append(resolved_input_file)
            output_file_list = list()
            for output_file, output_file_dict in process["output"].iteritems():
                #Check for variables
                resolved_output_file_list = self.resolve_variable(output_file, active_submodule)
                for resolved_output_file in resolved_output_file_list:
                    #Add files to manifest, but don't update:
                    if resolved_output_file not in self._submodule._module._analysis._manifest:
                        self._submodule._module._analysis._manifest[resolved_output_file] = active_submodule.name
                    output_file_list.append(active_submodule.name + "/" + resolved_output_file)
                    if output_file_dict["report_label"]:
                        label = output_file_dict["report_label"]
                        variable = output_file_dict["report_variable"]
                        sep = ", "
                        resolved_variable_list = self.resolve_variable(variable, active_submodule)
                        label = label.replace("${v}",sep.join(resolved_variable_list),1)
                        self._submodule._module._analysis.report.addToReport(label, active_submodule.name + "/" + resolved_output_file)

            #Now resolve the command
            command_str = process["command"]["cmd"]
            if process["command"]["format"] in ["slist"]:
                sep = " "
            elif process["command"]["format"] in ["sclist"]:
                sep = ";"
            else:
                sep = ","
            #First, the input variables:
            for input_file in process["command"]["input"].split(","):
                resolved_input_file_list = self.resolve_variable(input_file, active_submodule)
                cmd_input_file_list = list()
                for resolved_input_file in resolved_input_file_list:
                    if not isfile(resolved_input_file):
                        #If it does not, see if it exists in the file manifest
                        if resolved_input_file not in self._submodule._module._analysis._manifest:
                            #If it does not exist in the manifest or on system, complain
                            raise ValueError, "Required input file '%s' does not exist on system and not created by previously called module." % input_file
                        else:
                            cmd_input_file_list.append(self._submodule._module._analysis._manifest[resolved_input_file] + "/" + resolved_input_file)
                    else:
                        cmd_input_file_list.append(resolved_input_file)
                command_str = command_str.replace("${i}", sep.join(cmd_input_file_list),1)
            #Then the output variables:
            for output_file in process["command"]["output"].split(","):
                resolved_output_file_list = self.resolve_variable(output_file, active_submodule)
                cmd_output_file_list = list()
                for resolved_output_file in resolved_output_file_list:
                    cmd_output_file_list.append(active_submodule.name + "/" + resolved_output_file)
                    #Update ownership in manifest
                    self._submodule._module._analysis._manifest[resolved_output_file] = active_submodule.name
                command_str = command_str.replace("${o}",sep.join(cmd_output_file_list),1)
            #Finally, the variables
            for variable in process["command"]["variable"].split(","):
                resolved_variable_list = self.resolve_variable(variable, active_submodule)
                command_str = command_str.replace("${v}",sep.join(resolved_variable_list),1)
            command_str = "\tmkdir -p %s/\n\t%s" % (active_submodule.name,command_str)
            self._submodule._module._analysis.makefile.addProcess(input_file_list, output_file_list, command_str)
            
            

    #Probably the most complex method in this entire piece of software
    def resolve_variable(self, in_variable, active_submodule):
        #First, find the variables that we need to resolve
        variables = find_variables(in_variable)
        if not variables:
            return [in_variable]
        replacement_dict={}
        for variable in variables:
            #Take out the ${} from the variable
            variable = variable[2:-1]
            #Input variable resolution:
            #First check if it is a local or global variable
            #If local, get the local submodule and look for the variable there
            if variable.count(":") == 0:
                #Local submodule
                #Look to see if the variable is in the active submodule's argument list
                if variable in active_submodule._args:
                    replacement_dict[variable] = [active_submodule._args[variable]]
                elif variable == "PWD":
                    replacement_dict[variable] = [active_submodule.name]
                elif not active_submodule._submodule._input.getValuesForInput(variable)["required"]:
                    replacement_dict[variable] = ""
                else:
                    raise ValueError, "Cannot resolve variable %s, not found in submodule %s, module %s" % (variable, self._submodule.name, self._submodule._module.name)   
            else:
                #Global submodule
                module_name = variable.split(":")[0]
                variable = variable.split(":")[1]
                active_submodules = self._submodule._module._analysis.getActiveSubmodulesByModuleName(module_name)
                resolved_variables = list()
                for submodule in active_submodules:
                    #Look to see if the variable is in the active submodule's argument list
                    if variable in submodule._args:
                        resolved_variables.append(submodule._args[variable])
                replacement_dict[module_name+":"+variable] = resolved_variables
        #Check if the replacement lists are all the same size
        replace_max = max(map(len, replacement_dict.values()))
        #A variable should only be found in 1 module, or all activated submodules
        #Any other combination is too difficult to deal with in an automated fashion
        if replace_max != 1:
            for variable, replacement_list in replacement_dict.iteritems():
                if len(replacement_list) == 1:
                    #This recycles values that are 
                    replacement_dict[variable] = replacement_list*replace_max
                elif len(replacement_list) != replace_max:
                    raise ValueError, "Replacement list not 1 or equal to the replacement max"
        replacement_list = apply(zip, replacement_dict.values())
        to_replace = replacement_dict.keys()
        replaced_strings = list()
        for i in range(0, len(replacement_list)):
            for j in range(0, len(to_replace)):
                if replacement_list[i][j] == "":
                    replacement_string = ""
                else:
                    replacement_string = in_variable.replace("${"+to_replace[j]+"}", replacement_list[i][j])
            replaced_strings.append(replacement_string)
        return replaced_strings
    
class AxInfo(object):
    def __init__(self, submodule, xml_obj):
        #Give access to the submodule that originates this object
        self._submodule = submodule
        #Structure that stores all pertinent data
        self._values = {"input":{},"help":{"text":"No description given."}}
        #xml_obj is the <input> sections (including <input> tags)
        #There should only be one of these
        #Populate the values from the XML object
        for node in xml_obj.item(0).childNodes:
            if node.nodeType == xml.Node.ELEMENT_NODE:
                if node.nodeName == "command":
                #Get all of the information
                    label = node.getAttribute("label")
                    cmd = node.getAttribute("cmd")
                    self._values["command"] = {"label":label, "cmd":cmd}
                elif node.nodeName == "help":
                    text = node.getAttribute("text")
                    self._values["help"] = {"text":text}
                elif node.nodeName == "input":
                    name = node.getAttribute("name")
                    text = node.getAttribute("text")
                    self._values["input"][name] = text
                    
    def createMakefileString(self):
        makefile_string = ""
        for label, cmd in self._values:
            makefile_string += "\t@echo \"%s\"\n\t%s >> versions.log\n"
        return makefile_string

#Find variables in a string
def find_variables(source_str):
    #Pull out everything that is inside a "${}"
    return re.findall("\$\{.*?\}",source_str)
