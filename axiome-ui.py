#!/usr/bin/env python
# encoding: utf-8

import npyscreen as nps
from axiome_modules import AxiomeAnalysis
from os.path import dirname

source_dir = dirname(__file__)

class AXIOMEUI(nps.NPSAppManaged):
    def __init__(self, AxAnal, *args, **keywords):
        self.AxAnal = AxAnal
        super(AXIOMEUI, self).__init__(*args, **keywords)
        
    def onStart(self):
        #Load modules and submodules:
        self.current_module = 0
        self._display_modules = []
        nps.FIX_MINIMUM_SIZE_WHEN_CREATED = False
        #Tell the user what is going on
        for module in self.AxAnal._modules:
			if module.name != "source":
				self._display_modules.append(module.name)
				self.registerForm(module.name, ModuleForm(module, parentApp=self))
        self.registerForm("MAIN", IntroForm(parentApp=self))  

def addFloatWidget(form, name, label, minimum, maximum, default=0, step=0.01):
    return form.add_widget_intelligent(TitleFloatSlider, out_of=maximum, lowest=minimum, name=label, value=default, step=0.01)

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
        message="""Welcome to AXIOME\nTo navigate through the UI, use arrow keys or TAB.
            \nENTER will select an option, and SPACE will deselect an option.\nRequirements for the analysis:
            \n\t- Sequence data in paired-end FASTQ or FASTA format
            \n\t- Metadata mapping in tab-separated or comma-separated spreadsheet format (samples as rows, metadata titles as columns)
            \n\t- File mapping in tab-separated or comma-separated spreadsheet format"""
        nps.notify_confirm(message=message, title="Message", form_color='STANDOUT', wrap=True, wide=True, editw=1)
        self.name = "Select Pipeline Steps"
        #Fill with each module's submodule lists
        for module in self.parentApp.AxAnal._modules:
			#Build the submodule choices
			values = []
			for submodule in module._submodules:
				values.append(submodule.name)
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
				self.add_widget_intelligent(widget, name="Source Data Mapping File", max_height=3)
			else:
				self.add_widget_intelligent(widget, name=module._value["label"]+":", values=values, value=value, max_height=len(values)+2, scroll_exit=True)

    def afterEditing(self):
		#Put the current module choices in here
        self.parentApp.setNextForm(self.parentApp._display_modules[self.parentApp.current_module])
       
    def on_cancel(self):
        nps.notify_wait(message="Exiting is not yet implemented. Press Ctrl+c to kill the program.", title=":(", form_color="STANDOUT", wide=True)
        #Override the auto-exit
        self.editing = True
        
class ModuleForm(nps.FormMultiPageAction):
    def __init__(self, module, *args, **keywords):
        self.module = module
        super(ModuleForm, self).__init__(*args, **keywords)
    
    def on_cancel(self):
        if self.parentApp.current_module > 0:
            self.parentApp.current_module -= 1
        else:
			self.parentApp.current_module = -1
        self.exit_editing()
    
    def on_ok(self):
        if self.parentApp.current_module < (len(self.parentApp._display_modules) - 1):
            self.parentApp.current_module += 1
        self.exit_editing()
    
    def create(self):
        self.CANCEL_BUTTON_TEXT = "Previous"
        self.OK_BUTTON_TEXT = "Next"
        self.name = self.module._value["label"]
        #Populate the widgets based on the submodule requirements
        for submodule in self.module._submodules:
			AxInput = submodule._input
			self.add_widget_intelligent(nps.TitleFixedText, name="Submodule: " + submodule.name)
			for name, requirement in AxInput._values.iteritems():
				widget_type = requirement["type"]
				if widget_type == "float":
					float(requirement["default"])
					self.add_widget_intelligent(TitleFloatSlider, out_of=float(requirement["max"]), lowest=float(requirement["min"]), name=requirement["label"]+":", value=float(requirement["default"]), step=0.01)
				elif widget_type == "int":
					self.add_widget_intelligent(TitleFloatSlider, out_of=int(requirement["max"]), lowest=int(requirement["min"]), name=requirement["label"]+":", value=int(requirement["default"]), step=1)
				elif widget_type == "text":
					self.add_widget_intelligent(nps.TitleText, name=requirement["label"]+":", value=requirement["default"], max_height=3)
				elif widget_type == "file":
					self.add_widget_intelligent(nps.TitleFilenameCombo, name=requirement["label"]+":", max_height=3)

    def afterEditing(self):
        if self.parentApp.current_module >= 0:
            self.parentApp.setNextForm(self.parentApp._display_modules[self.parentApp.current_module])
        else:
            self.parentApp.setNextForm("MAIN")
        


if __name__ == "__main__":
    AxAnal = AxiomeAnalysis(None)
    App = AXIOMEUI(AxAnal)
    App.run()   
