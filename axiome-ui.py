#!/usr/bin/env python
# encoding: utf-8

import npyscreen as nps
from axiome_modules import AxiomeAnalysis, AxiomeModule, AxiomeSubmodule
from os.path import dirname

source_dir = dirname(__file__)

def addFloatWidget(form, name, label, minimum, maximum, default=0, step=0.01):
    return form.add_widget_intelligent(TitleFloatSlider, out_of=maximum, lowest=minimum, name=label, value=default, step=0.01)
    
def makeForm(input_dict, *args, **keywords):
    return ModuleForm({},*args, **keywords)

class AXIOMEUI(nps.NPSAppManaged):
    def onStart(self):
        #Load modules and submodules:
        self.current_module = 0
        self.AXAnal = AxiomeAnalysis(None, source_dir + "/res/master.xml", source_dir + "/res/test/Makefile")
        nps.FIX_MINIMUM_SIZE_WHEN_CREATED = False
        #Tell the user what is going on
        for module in self.AXAnal.module_list:
            fm = makeForm({},name=module.getModuleName())
            self.registerForm(module.getModuleName(), fm)
        self.STARTING_FORM = self.AXAnal.module_list[0].getModuleName()
        self.registerForm("MAIN", IntroForm())  

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
        self.OK_BUTTON_TEXT = "Next"
        self.CANCEL_BUTTON_TEXT = "Exit"
        message="""Welcome to AXIOME\nTo navigate through the UI, use arrow keys or TAB.
            \nENTER will select an option, and SPACE will deselect an option.\nRequirements for the analysis:
            \n\t- Sequence data in paired-end FASTQ or FASTA format
            \n\t- Metadata mapping in tab-separated or comma-separated spreadsheet format (samples as rows, metadata titles as columns)
            \n\t- File mapping in tab-separated or comma-separated spreadsheet format"""
        nps.notify_confirm(message=message, title="Message", form_color='STANDOUT', wrap=True, wide=True, editw=1)
        self.name= "Select Pipeline Steps"
        #Fill with each module's submodule lists
        mapping = self.add_widget_intelligent(nps.TitleSelectOne, name="Metadata Mapping:", values=["Copy"], value=[0,], max_height=3, scroll_exit=True)
        source = self.add_widget_intelligent(nps.TitleFilenameCombo, name = "Source Data Mapping File:",max_height=3)
        merge_sources = self.add_widget_intelligent(nps.TitleSelectOne, name="Source Data Merge Method:", values=["Cat"], value=[0,], max_height=3, scroll_exit=True)
        cluster = self.add_widget_intelligent(nps.TitleSelectOne, name="Cluster Method:", values=["cd-hit","qiime-cdhit","qiime-uclust", "swarm", "uclust", "uparse"], value=[0,], max_height=8, scroll_exit=True)
        rep_set = self.add_widget_intelligent(nps.TitleSelectOne, name="Rep Set Method:", values=["longest", "random", "most_frequent"], value=[0,], max_height=5, scroll_exit=True)
        chimera = self.add_widget_intelligent(nps.TitleMultiSelect, name="Chimera Checking:", values=["uchime"],max_height=3,scroll_exit=True)
        classification = self.add_widget_intelligent(nps.TitleSelectOne, name="Classification Method:", values=["rdp", "blast", "rtax"], value=[0,], max_height=5, scroll_exit=True)
        otu_table = self.add_widget_intelligent(nps.TitleSelectOne, name="OTU Table Creation:", values=["qiime"], value=[0,], max_height=3, scroll_exit=True)
        otu_filter = self.add_widget_intelligent(nps.TitleMultiSelect, name="OTU Table Filter:", values=["qiime", "taxonomy"],max_height=4,scroll_exit=True)
        #May need a try catch on the add_widget_intelligent? What if it can't fit in the terminal screen?
        analysis = self.add_widget_intelligent(nps.TitleMultiSelect, name="Analyses", values=["MRPP","NMDS","PCoA","taxaplot","alpha_rarefaction","UniFrac PCoA","duleg_indicator_species","NMF","heatmap","venn"],max_height=12, scroll_exit=True)

    def afterEditing(self):
        self.parentApp.setNextForm(self.parentApp.AXAnal.module_list[self.parentApp.current_module].getModuleName())
       
    def on_cancel(self):
        nps.notify_wait(message="Exiting is not yet implemented. Press Ctrl+c to kill the program.", title=":(", form_color="STANDOUT", wide=True)
        #Override the auto-exit
        self.editing = True
        
class ModuleForm(nps.FormMultiPageAction):
    def __init__(self, input_dict, *args, **keywords):
        self.input_dict = input_dict
        super(ModuleForm, self).__init__(*args, **keywords)
    
    def on_cancel(self):
        if self.parentApp.current_module > 0:
            self.parentApp.current_module -= 1
        else:
			self.parentApp.current_module = -1
        self.exit_editing()
    
    def on_ok(self):
        if self.parentApp.current_module < (len(self.parentApp.AXAnal.module_list) - 1):
            self.parentApp.current_module += 1
        self.exit_editing()
    
    def create(self):
        self.FIX_MINIMUM_SIZE_WHEN_CREATED = False
        self.CANCEL_BUTTON_TEXT = "Previous"
        self.OK_BUTTON_TEXT = "Next"

    def afterEditing(self):
        if self.parentApp.current_module >= 0:
            self.parentApp.setNextForm(self.parentApp.AXAnal.module_list[self.parentApp.current_module].getModuleName())
        else:
            self.parentApp.setNextForm("MAIN")
        


if __name__ == "__main__":
    App = AXIOMEUI()
    App.run()   
