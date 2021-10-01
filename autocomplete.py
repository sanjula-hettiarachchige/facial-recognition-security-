from tkinter import *
import re


class Auto_Complete_Entry(Entry):
    def __init__(self, lista, dropdown_width, x=0, y=0, *args, **kwargs):
        
        Entry.__init__(self, *args, **kwargs)
        
        self.lista = lista
        self.y = y
        self.x = x
        self.width = dropdown_width
        self.var = self["textvariable"]
        if self.var == '':
            self.var = self["textvariable"] = StringVar()

        self.var.trace('w', self.changed)
        self.bind("<Right>", self.selection)
        self.bind("<Return>", self.selection)
        self.bind("<Up>", self.up)
        self.bind("<Down>", self.down)
        
        self.lb_up = False

    def changed(self, name, index, mode):
        if self.var.get().lower() == '':
            try:
                self.lb.destroy()
            except:
                pass
            self.lb_up = False
        else:
            words = self.comparison()
            if words:            
                if not self.lb_up:
                    height = self.winfo_y()+self.winfo_height()+self.y
                    if height>=411:
                        height = 411
                    self.lb = Listbox(self.master, width=self.width, height=3)
                    self.lb.bind("<Double-Button-1>", self.selection)
                    self.lb.bind("<Right>", self.selection)
                    self.lb.place(x=self.winfo_x()+self.x, y=height)
                    self.lb_up = True
                
                self.lb.delete(0, END)
                for w in words:
                    self.lb.insert(END,w)
            else:
                if self.lb_up:
                    self.lb.destroy()
                    self.lb_up = False
            if self.var.get().lower() in words:
                self.lb.destroy()
                self.lb_up = False
             
        
    def selection(self, event):

        if self.lb_up:
            self.var.set(self.lb.get(ACTIVE))
            self.lb.destroy()
            self.lb_up = False
            self.icursor(END)

    def up(self, event):

        if self.lb_up:
            if self.lb.curselection() == ():
                index = '0'
            else:
                index = self.lb.curselection()[0]
            if index != '0':                
                self.lb.selection_clear(first=index)
                index = str(int(index)-1)                
                self.lb.selection_set(first=index)
                self.lb.activate(index) 

    def down(self, event):

        if self.lb_up:
            if self.lb.curselection() == ():
                index = '0'
            else:
                index = self.lb.curselection()[0]
            if index != END:                        
                self.lb.selection_clear(first=index)
                index = str(int(index)+1)        
                self.lb.selection_set(first=index)
                self.lb.activate(index) 

    def comparison(self):
        pattern = re.compile('.*' + self.var.get().lower() + '.*')
        return [w for w in self.lista if re.match(pattern, w)]
