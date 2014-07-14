#!/usr/bin/env python
# encoding: utf-8

import npyscreen as nps
from axiome_modules import AxiomeAnalysis
from os.path import dirname

source_dir = dirname(__file__)

class AXIOMEUI(nps.NPSAppManaged):
    def __init__(self, AxAnal, *args, **keywords):
        self.AxAnal = AxAnal
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
                form = self.createSubmoduleForm(module_name, submodule_name)
                if form:
                    new_submodule_forms_data.append({"module_name":module_name, "submodule_name":submodule_name, "form":form, "copy_number":0, "registered":False})
        #Clear the page display list
        self._display_pages = list()
        for form_data in new_submodule_forms_data:
            formid = form_data["module_name"]+"_"+form_data["submodule_name"]+"_"+str(form_data["copy_number"])
            self.registerForm(formid,form_data["form"])
            self._display_pages.append(formid)
        self.submodule_forms_data = new_submodule_forms_data
            
    def createSubmoduleForm(self, module_name, submodule_name):
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
        form = SubmoduleForm(module, submodule, parentApp=self)
        form.add_widget_intelligent(nps.TitleFixedText, w_id="submodule_title_"+submodule.name, name="Submodule: " + submodule.name)
        for requirement in AxInput._values:
            widget_type = requirement["type"]
            if widget_type == "float":
                float(requirement["default"])
                form.add_widget_intelligent(TitleFloatSlider, w_id=requirement["name"], out_of=float(requirement["max"]), lowest=float(requirement["min"]), name=requirement["label"]+":", value=float(requirement["default"]), step=0.01)
            elif widget_type == "int":
                form.add_widget_intelligent(TitleFloatSlider, w_id=requirement["name"], out_of=int(requirement["max"]), lowest=int(requirement["min"]), name=requirement["label"]+":", value=int(requirement["default"]), step=1)
            elif widget_type == "text":
                form.add_widget_intelligent(nps.TitleText, w_id=requirement["name"], name=requirement["label"]+":", value=requirement["default"], max_height=3)
            elif widget_type == "file":
                form.add_widget_intelligent(nps.TitleFilenameCombo, w_id=requirement["name"], name=requirement["label"]+":", max_height=3)
        #Add the "ADD/REMOVE" buttons here
        return form
        
    def createAxiomeFile(self, save_path):
        pass
        
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

    def afterEditing(self):
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
        
    def on_ok(self):
        source_file_widget = None
        for widget_info in self._widget_list:
            if widget_info["module_name"] == "source":
                source_file_widget = widget_info["widget"]
                break
        if source_file_widget:
            source_file_path = source_file_widget.value
            if not source_file_path:
                nps.notify_confirm(message="Source file mapping required")
                self.editing = True
                return
            if not self.sourceFileCheck(source_file_path):
                nps.notify_confirm(message="Error in source file mapping")
                self.editing = True
                return
        else:
            raise ValueError, "No widget found for required module 'source'"
       
    def on_cancel(self):
        nps.notify_wait(message="Exiting is not yet implemented. Press Ctrl+c to kill the program.", title=":(", form_color="STANDOUT", wide=True)
        #Override the auto-exit
        self.editing = True
        
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
    def create(self):
        self.name = "Save AXIOME File"
        self.ALLOW_RESIZE = False
        self.OK_BUTTON_TEXT = "Save"
        self.CANCEL_BUTTON_TEXT = "Previous"
        self.add_widget_intelligent(nps.TitleFilenameCombo, select_dir=True, w_id="save_directory", name="Save File Directory...", max_height=3)
        self.add_widget_intelligent(nps.TitleText, w_id="save_filename", name="Save Filename", max_height=3)
        
    def on_cancel(self):
        self.parentApp.current_page -= 1
        self.parentApp.setNextForm(self.parentApp._display_pages[self.parentApp.current_page])
        
    def on_ok(self):
        pass
        
class SubmoduleForm(nps.FormMultiPageAction):
    def __init__(self, module, submodule, *args, **keywords):
        #Keep it from crashing when terminal size changes
        self.ALLOW_RESIZE = False
        self.module = module
        self.submodule = submodule
        super(SubmoduleForm, self).__init__(*args, **keywords)
    
    def on_cancel(self):
        if self.parentApp.current_page > 0:
            self.parentApp.current_page -= 1
        else:
            self.parentApp.current_page = -1
        self.exit_editing()
    
    def on_ok(self):
        if self.parentApp.current_page <= (len(self.parentApp._display_pages) - 1):
            self.parentApp.current_page += 1
        self.exit_editing()
    
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

if __name__ == "__main__":
    AxAnal = AxiomeAnalysis(None)
    App = AXIOMEUI(AxAnal)
    App.run()   
