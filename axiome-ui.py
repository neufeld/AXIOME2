#!/usr/bin/env python
# encoding: utf-8

import npyscreen as nps
from axiome_modules import AxiomeAnalysis, getWorkflowList
from os.path import dirname, abspath

source_dir = dirname(abspath(__file__))

class AXIOMEUI(nps.NPSAppManaged):
    def __init__(self, *args, **keywords):
        self.submodule_forms_data = list()
        self.source_definitions = list()
        super(AXIOMEUI, self).__init__(*args, **keywords)

    def onStart(self):
        #Load modules and submodules:
        self.current_page = 0
        self._display_pages = []
        nps.FIX_MINIMUM_SIZE_WHEN_CREATED = False
        self.registerForm("MAIN", IntroForm(parentApp=self))
        self.registerForm("SAVE", SaveForm(parentApp=self))
                    
    def buildSubmoduleForms(self, selected_submodules):
        new_submodule_forms_data = list()
        for names in selected_submodules:
            module_name = names["module_name"]
            submodule_name = names["submodule_name"]
            #For each selected module+submodule, check if it is in the list
            inserted = False
            for form in self.submodule_forms_data:
                if (module_name == form["module_name"]) and (submodule_name == form["submodule_name"]):
                    new_submodule_forms_data.append(form)
                    inserted = True
            #If not found, make a new dictionary to hold information
            if not inserted:
                form = self.createSubmoduleForm(module_name, submodule_name, 0)
                if form:
                    new_submodule_forms_data.append({"module_name":module_name, "submodule_name":submodule_name, "form":form, "copy_number":0, "registered":False})
        #Clear the page display list
        self._display_pages = list()
        for form_data in new_submodule_forms_data:
            formid = form_data["module_name"]+"_"+form_data["submodule_name"]+"_"+str(form_data["copy_number"])
            self.registerForm(formid,form_data["form"])
            self._display_pages.append(formid)
        self.submodule_forms_data = new_submodule_forms_data
            
    def createSubmoduleForm(self, module_name, submodule_name, copy_number):
        #Grab the AxInput for the submodule
        module = self.AxAnal.getModuleByName(module_name)
        if not module:
            raise ValueError, "Cannot find module: %s" % module_name
        submodule = module.getSubmoduleByName(submodule_name)
        if not submodule:
            raise ValueError, "Cannot find module: %s" % submodule_name
        AxInput = submodule._input
        if not AxInput._values:
            return False
        #Create the form
        form = SubmoduleForm(module, submodule, copy_number, parentApp=self)
        if module._value["multi"]:
            form.add_widget_intelligent(nps.TitleFixedText, w_id="submodule_title_"+submodule.name, name="Submodule: %s (%s)" % (submodule.name, str(copy_number+1)))
        else:
            form.add_widget_intelligent(nps.TitleFixedText, w_id="submodule_title_"+submodule.name, name="Submodule: %s" % submodule.name)
        for requirement in AxInput._values:
            widget_type = requirement["type"]
            if widget_type == "float":
                form.add_widget_intelligent(TitleFloatSlider, w_id=requirement["name"], out_of=float(requirement["max"]), lowest=float(requirement["min"]), name=requirement["label"]+":", value=float(requirement["default"]), step=0.01)
            elif widget_type == "int":
                form.add_widget_intelligent(TitleFloatSlider, w_id=requirement["name"], out_of=int(requirement["max"]), lowest=int(requirement["min"]), name=requirement["label"]+":", value=int(requirement["default"]), step=1)
            elif widget_type == "text":
                form.add_widget_intelligent(nps.TitleText, w_id=requirement["name"], name=requirement["label"]+":", value=requirement["default"], max_height=3)
            elif widget_type == "file":
                form.add_widget_intelligent(nps.TitleFilenameCombo, w_id=requirement["name"], name=requirement["label"]+":", max_height=3)
            required = requirement["required"]
            form._value["input"].append({"name":requirement["name"],"required":required, "type":requirement["type"]})
        #If you can have multiple submodules, then add an add/remove button
        #to duplicate submodules
        if module._value["multi"]:
            form.nextrely+=1
            form.add_widget_intelligent(AddFormButton, name="Add Copy of Submodule", w_id="submodule_add")
            form.add_widget_intelligent(RemoveFormButton, name="Remove Copy of Submodule", w_id="submodule_remove")
        return form

class IntroForm(nps.FormMultiPageAction):
    def create(self):
        #Keep it from crashing when terminal size changes
        self.ALLOW_RESIZE = False
        self.OK_BUTTON_TEXT = "Next"
        self.CANCEL_BUTTON_TEXT = "Exit"
        self._widget_list = []
        message="""Welcome to AXIOME\nTo navigate through the UI, use arrow keys or TAB.
            \nENTER will select an option, and SPACE will deselect an option.
            \nRequirements for the analysis:
            \n\t- File mapping in tab-separated spreadsheet format (.tsv)
            \n\t- Metadata mapping in tab-separated spreadsheet format (.tsv)"""
        nps.notify_confirm(message=message, title="Message", form_color='STANDOUT', wrap=True, wide=True, editw=1)
        self.name = "Select Workflow"
        #Get the possible workflows from the master.xml file
        workflow_list = getWorkflowList()
        try:
            value = workflow_list.index("Default")
        except:
            value = 0
        self.add_widget_intelligent(nps.TitleSelectOne, name="Select Workflow", w_id="select_workflow", values=workflow_list, value=value, max_height=len(workflow_list)+2, scroll_exit=True)
        
    def on_ok(self):
        #Create the ModuleForm
        workflow = self.get_widget("select_workflow").values[self.get_widget("select_workflow").value[0]]
        self.parentApp.AxAnal = AxiomeAnalysis(None, workflow)
        module_form = ModuleForm(parentApp=self.parentApp)
        self.parentApp.registerForm("MODULE",module_form)
        self.parentApp.setNextForm("MODULE")
        
        
    def on_cancel(self):
        nps.notify_wait(message="Exiting is not yet implemented. Press Ctrl+c to kill the program.", title=":(", form_color="STANDOUT", wide=True)
        #Override the auto-exit
        self.editing = True

class ModuleForm(nps.FormMultiPageAction):
    def create(self):
        #Keep it from crashing when terminal size changes
        self.ALLOW_RESIZE = False
        self.OK_BUTTON_TEXT = "Next"
        self.CANCEL_BUTTON_TEXT = "Previous"
        self._widget_list = []
        self.name = "Select Pipeline Steps"
        #Fill with each module's submodule lists
        for module in self.parentApp.AxAnal._modules:
            #Build the submodule choices
            values = []
            for submodule in module._submodules:
                values.append(submodule.name)
            if values:
                #Two options: multi or not
                if module._value["multi"]:
                    widget = nps.TitleMultiSelect
                    value = None
                else:
                    widget = nps.TitleSelectOne
                    value = 0
                #Special case: mapping file, we want to select a spreadsheet
                if module.name == "source":
                    widget = nps.TitleFilenameCombo
                    choice_widget = self.add_widget_intelligent(widget, w_id="module_source", name="Source Data Mapping File", max_height=3)
                    #For consistent spacing
                    self.nextrely += 1
                else:
                    #Sort out the values, given the defaults
                    defaults = list()
                    for i in range(0, len(values)):
                        if values[i] in module._value["default"]:
                            defaults.append(i)
                    if defaults:
                        value = defaults
                    choice_widget = self.add_widget_intelligent(widget, name=module._value["label"]+":", w_id="module_"+module.name, values=values, value=value, max_height=len(values)+2, scroll_exit=True)
                self._widget_list.append({"module_name":module.name,"widget":choice_widget})    
        
    def on_ok(self):
        source_file_widget = self.get_widget("module_source")
        source_file_path = source_file_widget.value
        if not source_file_path:
            nps.notify_confirm(message="Source file mapping required")
            self.editing = True
            return
        if not self.sourceFileCheck(source_file_path):
            nps.notify_confirm(message="Error in source file mapping")
            self.editing = True
            return
        #Collect information on the selected widgets
        selected_submodules = list()
        for widget_info in self._widget_list:
            module_name = widget_info["module_name"]
            widget = widget_info["widget"]
            if type(widget.value) is list:
                for choice in widget.value:
                    selected_submodules.append({"module_name":module_name,"submodule_name":widget.values[choice]})
        nextForm = self.parentApp.buildSubmoduleForms(selected_submodules)
        self.parentApp.current_page = 0
        self.parentApp.setNextForm(self.parentApp._display_pages[0])
       
    def on_cancel(self):
        self.parentApp.setNextForm("MAIN")
        
    def sourceFileCheck(self, source_file_path):
    #Go through each line of the sources file and verify the contents
        with open(source_file_path) as source_file:
            #Clear the old definitions out
            self.parentApp.source_definitions = list()
            column_headers = None
            for definition in source_file:
                #Ignore comment lines
                if definition[0] == "#":
                    continue
                else:
                    #We need to detect the column headers row
                    #We are using the EBI metadata sheet as our template here
                    if "sample_alias" in definition.split("\t"):
                        column_headers = definition
                    else:
                        if not column_headers:
                            return False
                        #Special column headers:
                        #axiome_submodule: name of source submodule that controls the sample
                        sample_dict = dict(zip(column_headers.strip().split("\t"), definition.strip().split("\t")))
                        try:
                            submodule_name = sample_dict["axiome_submodule"]
                        except KeyError:
                            raise KeyError, "Required column header 'axiome_submodule' not found"
                        #Get the submodule
                        submodule = self.parentApp.AxAnal.getModuleByName("source").getSubmoduleByName(submodule_name)
                        #Get the AxInput object
                        AxInput = submodule._input
                        #Make sure the requirements are met
                        if AxInput.requirementsMet(sample_dict):
                            #Store the dict
                            self.parentApp.source_definitions.append(sample_dict)
                        else:
                            raise ValueError, str(sample_dict)
                            #**TODO** Make this a persistent popup warning when trying to exit
                            #the intro form, not a raised error
                            #return False
            if not self.parentApp.source_definitions:
                return False
            return True
            
class SaveForm(nps.FormMultiPageAction):
    def __init__(self, *args, **keywords):
        super(SaveForm, self).__init__(*args, **keywords)
        
    def create(self):
        self.name = "Save AXIOME File"
        self.ALLOW_RESIZE = False
        self.OK_BUTTON_TEXT = "Save"
        self.CANCEL_BUTTON_TEXT = "Previous"
        self.add_widget_intelligent(nps.TitleFilenameCombo, select_dir=True, w_id="save_directory", name="Save File Directory...", max_height=3)
        self.add_widget_intelligent(nps.TitleText, w_id="save_filename", name="Save Filename", max_height=3)
        
    def on_cancel(self):
        #Go back to the last page
        self.parentApp.current_page -= 1
        self.parentApp.setNextForm(self.parentApp._display_pages[self.parentApp.current_page])
        
    def on_ok(self):
        #Get the save file path
        file_dir = self.get_widget("save_directory").value
        if not file_dir:
            nps.notify_wait("Save File Directory must be specified.", title="Error", form_color='STANDOUT', wrap=True, wide=True)
            self.editing = True
            return
        file_name = self.get_widget("save_filename").value
        if not file_name:
            nps.notify_wait("Save Filename must be specified.", title="Error", form_color='STANDOUT', wrap=True, wide=True)
            self.editing = True
            return
        #Options are OK. Now write the file:
        with open(file_dir + "/" + file_name,'w') as out_ax:
            #Start with the XML header
            #**TODO** Different workflows
            #We are manually writing XML, because that's how I roll
            ax_file_string = '<?xml version="1.0"?>\n<axiome workflow="%s">\n' % self.parentApp.AxAnal.workflow
            submodules = list()
            for widget_info in self.parentApp.getForm("MODULE")._widget_list:
                module_name = widget_info["module_name"]
                #Get the selection(s) from the selection widget
                widget = widget_info["widget"]
                selections = widget.value
                if module_name != "source":
                    for choice in selections:
                        submodules.append([module_name, widget.values[choice]])
                else:
                    submodules.append(["source",None])
            #For each module, go through the submodule page list to find a match
            for submodule in submodules:
                module_name = submodule[0]
                submodule_name = submodule[1]
                #Special case: source
                if module_name == "source":
                    mapping_file = self.parentApp.getForm("MODULE").get_widget("module_source").value
                    ax_file_string += self.file_mapping_to_ax(mapping_file)
                else:
                    found = False
                    for submodule_form in self.parentApp.submodule_forms_data:
                        if (submodule_form["module_name"] == module_name) & (submodule_form["submodule_name"] == submodule_name):
                            found = True
                            #If it matches, write a line for it
                            def_string = ""
                            requirements = submodule_form["form"]._value
                            for item in requirements["input"]:
                                #Get the widget and its value
                                widget_id = item["name"]
                                widget_value = submodule_form["form"].get_widget(widget_id).value
                                if widget_value:
                                    def_string += ' %s="%s"' % (widget_id, widget_value)
                            ax_file_string += '\t<%s method="%s"%s/>\n' % (module_name, submodule_name, def_string)
                    if not found:
                        ax_file_string += '\t<%s method="%s"/>\n' % (module_name, submodule_name)
            ax_file_string += "</axiome>"
            out_ax.write(ax_file_string)
        #**TODO** Make notify_confirm, allowing user to go back or exit
        nps.notify_wait("File saved successfully to %s/%s. Ctrl+C to exit." % (file_dir, file_name), title="Saved!", form_color='STANDOUT', wrap=True, wide=True)
        
    def file_mapping_to_ax(self, mapping_file):
        with open(mapping_file) as mapping:
            #Clear the old definitions out
            self.parentApp.source_definitions = list()
            column_headers = None
            source_defs = ""
            for definition in mapping:
                #Ignore comment lines
                if definition[0] == "#":
                    continue
                else:
                    #We need to detect the column headers row
                    #We are using the EBI metadata sheet as our template here
                    if "sample_alias" in definition.split("\t"):
                        column_headers = definition
                    else:
                        if not column_headers:
                            return False
                        #Start building the line
                        source_variables = ""
                        sample_dict = dict(zip(column_headers.strip().split("\t"), definition.strip().split("\t")))
                        for header, value in sample_dict.iteritems():
                            if (value != "") & (header != 'axiome_submodule'):
                                source_variables += ' %s="%s"' % (header, value)
                        source_line = '\t<source method="%s"%s/>\n' % (sample_dict["axiome_submodule"], source_variables)
                        source_defs += source_line
        return source_defs
                        
        
class SubmoduleForm(nps.FormMultiPageAction):
    def __init__(self, module, submodule, copy_number, *args, **keywords):
        #Keep it from crashing when terminal size changes
        self.ALLOW_RESIZE = False
        self.module = module
        self.submodule = submodule
        self.copy_number = copy_number
        #Contain the important information about the form
        self._value = {"module_name":module.name, "submodule_name":submodule.name, "input":[]}
        super(SubmoduleForm, self).__init__(*args, **keywords)
    
    def on_cancel(self):
        if self.parentApp.current_page > 0:
            self.parentApp.current_page -= 1
        else:
            self.parentApp.current_page = -1
        #self.exit_editing()
    
    def on_ok(self):
        #Validate the input variables
        #Get the variables
        args = {}
        for input_item in self._value["input"]:
            name = input_item["name"]
            if self.get_widget(name).value:
                args[name] = self.get_widget(name).value
        if not(self.submodule._input.requirementsMet(args)):
            nps.notify_wait("Not all required input items for this module have been entered. Please check all fields.", title="Error", form_color='STANDOUT', wrap=True, wide=True)
            self.editing = True
        else:
            if self.parentApp.current_page <= (len(self.parentApp._display_pages) - 1):
                self.parentApp.current_page += 1
            #self.exit_editing()
    
    def create(self):
        self.CANCEL_BUTTON_TEXT = "Previous"
        self.OK_BUTTON_TEXT = "Next"
        self.name = self.module._value["label"]

    def afterEditing(self):
        if self.parentApp.current_page < 0:
            self.parentApp.setNextForm("MAIN")
            self.parentApp.current_page = 0
        elif self.parentApp.current_page <= (len(self.parentApp._display_pages) - 1): 
            self.parentApp.setNextForm(self.parentApp._display_pages[self.parentApp.current_page])
        else:
            self.parentApp.setNextForm("SAVE")

#Add/Remove Form button logic for submodule forms
class AddFormButton(nps.ButtonPress):
    def whenPressed(self):
        form = self.parent
        module_name = self.parent.module.name
        submodule_name = self.parent.submodule.name
        #Go through list of forms, and add it after all current forms of the same submodule
        found = False
        for i in range(0, len(form.parentApp.submodule_forms_data)):
            if (module_name == form.parentApp.submodule_forms_data[i]["module_name"]) & (submodule_name == form.parentApp.submodule_forms_data[i]["submodule_name"]):
                found = True
                copy_number = form.parentApp.submodule_forms_data[i]["copy_number"]+1
                insert_location = i+1
            elif found:
                break   
        #Create new form
        new_form = form.parentApp.createSubmoduleForm(module_name, submodule_name, copy_number)
        #Add to submodule forms list
        form.parentApp.submodule_forms_data.insert(insert_location, {"form":new_form, "submodule_name":submodule_name, "module_name":module_name, "copy_number":copy_number, "registered":False})
        #Register form and add to the list of formid's
        formid = module_name+"_"+submodule_name+"_"+str(copy_number)
        form.parentApp.registerForm(formid, new_form)
        form.parentApp._display_pages.insert(insert_location, formid)
        #Notify the user that it worked
        nps.notify_wait("New copy of submodule %s added as next page." % submodule_name, title="Submodule Duplicated", form_color='STANDOUT', wrap=True, wide=True)

class RemoveFormButton(nps.ButtonPress):
    def whenPressed(self):
        form = self.parent
        module_name = self.parent.module.name
        submodule_name = self.parent.submodule.name
        copy_number = self.parent.copy_number
        formid = module_name+"_"+submodule_name+"_"+str(copy_number)
        #Need to remove from the submodule_forms_data list and _display_pages list
        form.parentApp._display_pages.remove(formid)
        copy_count = 0
        for form_data in form.parentApp.submodule_forms_data:
            if (module_name == form_data["module_name"]) & (submodule_name == form_data["submodule_name"]) & (copy_number == form_data["copy_number"]):
                form.parentApp.submodule_forms_data.remove(form_data)
            elif (module_name == form_data["module_name"]) & (submodule_name == form_data["submodule_name"]):
                copy_count += 1
        #If the last one is removed, we need to unselect the IntroForm widget
        if copy_count == 0:
            ModuleForm = form.parentApp.getForm("MODULE")
            for widget_info in ModuleForm._widget_list:
                if module_name == widget_info["module_name"]:
                    for choice in widget_info["widget"].value:
                        if widget_info["widget"].values[choice] == submodule_name:
                            widget_info["widget"].value.remove(choice)
        nps.notify_wait("Deleted copy of submodule %s." % submodule_name, title="Submodule Removed", form_color='STANDOUT', wrap=True, wide=True)
        form.edit_return_value = True
        form.editing = False
        
#Custom Slider class that hits min and max properly
class FloatSlider(nps.Slider):
    def translate_value(self):
        stri = "%s" % self.value
        return stri

    def h_increase(self, ch):
        if (self.value + self.step <= self.out_of): self.value += self.step
        elif (self.value >= self.out_of - self.step) & (self.value <= self.out_of): self.value = self.out_of

    def h_decrease(self, ch):
        if (self.value - self.step >= self.lowest): self.value -= self.step
        elif (self.value <= self.step - self.lowest) & (self.value >= self.lowest): self.value = self.lowest

class TitleFloatSlider(nps.wgtitlefield.TitleText):
    _entry_type = FloatSlider

if __name__ == "__main__":
    App = AXIOMEUI()
    App.run()   
