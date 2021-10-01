from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
import sqlite3
import hashlib
from datetime import datetime, timedelta 
import numpy as np
import cv2
from PIL import Image, ImageTk
from threading import Thread
import os
import shutil 
from shutil import copyfile
import datepicker
import autocomplete
from xlwt import *
class Login:

	connection = sqlite3.connect('database.db') #Establishes a connection to the database
	db = connection.cursor()


	def __init__(self, master):
		self.master = master
		master.title("Login")
		self.username = StringVar()
		self.password = StringVar()
		self.welcome_label = Label(master, text="Welcome, please enter your username and password.")
		self.username_label = Label(master, text="Username:")
		self.password_label = Label(master, text="Password:")    
		self.username_entry = Entry(master, textvariable=self.username, width=30)
		self.password_entry = Entry(master, show="*", textvariable=self.password, width=30)
		self.welcome_label.grid(row=0, sticky=E, columnspan=2, padx=(10,10), pady=(10,10))
		self.username_label.grid(row=1, sticky=NSEW, padx=(5,5), pady=(5,5))
		self.password_label.grid(row=2, sticky=NSEW, padx=(5,5), pady=(5,5))
		self.username_entry.grid(row=1, column=1)
		self.password_entry.grid(row=2, column=1)
		self.login_button = Button(master, text="Login", width=10, command=lambda: self.login(self.username, self.password))
		self.login_button.bind("<Return>", lambda event: self.login(self.username, self.password))
		self.login_button.grid(row=3, columnspan=2, sticky=E, padx=(0,10), pady=(5,5))
		self.w = 320
		self.h = 140
		self.tries = 0
		centre(self.w, self.h, master)
		self.login_check()

	

	def login_check(self):
		self.db.execute("SELECT Setting_Value FROM Settings WHERE Setting=?", ("Login_Block_Time",)) #Query to retrieve the Login_Block_Time 
		login_block_time = self.db.fetchall()[0][0] #Retrieves Login_Block_Time from database
		login_block_time = datetime.strptime(login_block_time, '%d/%m/%y %H:%M:%S') #Converts string to datetime object format so that it can be compared
		current_time = datetime.now() #Gets the current date and time
		if login_block_time > current_time: #Checks whether the login_block_time is after the current time
			self.db.close() #Closes connection to the database
			self.master.destroy() #Closes the main login form window to block a login attempt
		else:
			pass #The login form will open as normal if the login attempt is after the login_block_time
      

	
	def login(self, username, password):
		global verify 
		global current_access_level #Declares global variable to hold current users access level
		global current_user_id #Declared global varibal to hold current users user_id
		username = username.get() #Retrieves value in the username entry box
		password = password.get() #Retrieves the value in the password entry box
		self.db.execute("SELECT User_Password FROM User WHERE User_Login=?", (username,)) #Query to extract the digest for the entered username
		db_password = self.db.fetchall() #Retrieves the digest for the username entered
		hashed_password = hashlib.sha1(password.encode('utf-8')) #Hashes the password using the SHA1 hashing algorithm
		hashed_password = hashed_password.hexdigest() #Extracts actual digest in hexadecimal form

		verify = False #Boolean variable will be true if login is successful
		if len(db_password) != 0: #Checks whether no passwords have been returned, means entered username does not exist
			if db_password[0][0] == hashed_password: #If passwords match, dashboard will open
				verify = True 
				#Queries database for current users access level and id
				self.db.execute("SELECT User_AccessLevel, User_Id From User WHERE User_Login=?", (username,)) 
				result = self.db.fetchall()
				current_access_level = result[0][0]
				current_user_id = result [0][1]
				self.db.close()
				self.master.destroy()
		
		if verify == False: #If login is not successful, tries will be increased by 1 and an error message will be displayed
			self.tries += 1
			messagebox.showerror("Access Denied", "The wrong details have been entered the wrong credentials. You have " + 
			str(3-self.tries) +" tries left") #Displays error message with number of tries left
			self.username_entry.delete(0, 'end') #Clears username entry box
			self.password_entry.delete(0, 'end') #Clears password entry box
			
		if self.tries == 3: #After the limit of tries has been reached
			self.block() #Will block anymore login attempts until the next minute
			self.master.destroy()

	def block(self):
		
		now = datetime.now() #Contains datetime object which has the current date and time
		next_min = datetime.now() + timedelta(minutes=1) #Adds one minute to the cureent time
		next_min = next_min.strftime("%d/%m/%y %H:%M:%S")
		self.db.execute("UPDATE Settings set Setting_Value=? WHERE Setting=?", (next_min,"Login_Block_Time",)) #Updates the record with new login block time
		self.connection.commit()
		self.db.close()



class Dashboard:
	def __init__(self, master):
		self.master = master
		master.title("Dashboard")
		self.menubar = Menu(master)
		self.manage_profile_menu = Menu(self.menubar, tearoff=0)
		self.manage_profile_menu.add_command(label="Add Profile", command=lambda: Thread(target=self.add_profile()).start())
		self.manage_profile_menu.add_command(label="Edit Profile", command=lambda: Thread(target=self.edit_profile()).start())
		self.menubar.add_cascade(label="Manage Profiles", menu=self.manage_profile_menu)	
		
		self.menubar.add_command(label="Reports", command=lambda: Thread(target=self.report()).start())
	
		self.menubar.add_command(label="Review", command=lambda: Thread(target=self.review()).start())
		
		self.manage_user_menu = Menu(self.menubar, tearoff=0)
		self.manage_user_menu.add_command(label="Add user", command=lambda: Thread(target=self.add_user()).start())
		self.manage_user_menu.add_command(label="Edit user", command=lambda: Thread(target=self.edit_user()).start())
		self.manage_user_menu.add_command(label="Change Password", command=lambda: Thread(target=self.change_password()).start())
		self.menubar.add_cascade(label="Manage Users", menu=self.manage_user_menu)
		
		self.menubar.add_command(label="Settings", command=lambda: Thread(target=self.settings()).start())
		master.config(menu=self.menubar)

		if current_access_level <=2:
			self.menubar.delete("Settings")
			self.manage_user_menu.delete("Add user")
			self.manage_user_menu.delete("Edit user")
		if current_access_level <=1:
			self.menubar.delete("Review")
			self.manage_profile_menu.delete("Add Profile")
			self.menubar.delete("Manage Profiles")
		if current_access_level == 0:
			self.menubar.delete("Reports")

		self.w = master.winfo_screenwidth()-10 #Adjusts width of window to make it fill the screen
		self.h = master.winfo_screenheight()-100 #Adjust height of window to take into account the taskbar on all devices
		self.x = 0
		self.y= 0
		master.geometry('%dx%d+%d+%d' % (self.w, self.h, self.x, self.y)) #Makes the size of the window so it is WxH in size and starts at (x,y)
		master.resizable(0,0) #Prevents window size from being changed 

		self.video_frame = Frame(master, width=self.w, height=self.h) #Creates a frame for the video feed
		self.video_frame.pack() 

		self.video_label = Label(self.video_frame) #Declares a label which will contain the video frame 
		self.video_label.pack()
		#self.cap = cv2.VideoCapture(1) #Defines connection between the program and the camera
		self.cap = cv2.VideoCapture("kevin.mp4") #Defines connection between the program and the camera
		thread1 = Thread(target=self.show_frame) #Defines thread for the show_frame method
		thread1.start() 

	def show_frame(self):	
		try:
			_, frame = self.cap.read() #Reads frame from camera
			cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA) #Converts frame to RGBA from BGR
			img = Image.fromarray(cv2_image) #Converts frame to Image object
			img = img.resize((self.w-10, self.h), Image.ANTIALIAS) #Resizes video frame to fit the dashboard window
			imgtk = ImageTk.PhotoImage(image=img) #Converts image 'img' to photoimage so it can be displayed in the window

			self.video_label.imgtk = imgtk
			self.video_label.configure(image=imgtk)
			self.video_label.after(10, self.show_frame) #Executes show_frame method every 10 milliseconds
		except:
			self.video_label.after(10, self.show_frame)



	def edit_user(self):
		user_root = Toplevel()
		user_root.attributes('-topmost', 'true')
		user_form = User_Form(user_root, "edit")

	def change_password(self):
		change_password_root = Toplevel()
		change_password_root.attributes('-topmost', 'true')
		change_password_form = Change_Password(change_password_root)

	def settings(self):
		settings_root = Toplevel()
		settings_root.attributes('-topmost', 'true')
		setting_form = Settings(settings_root)

	def review(self):
		review_log_root = Toplevel()
		review_log_root.attributes('-topmost', 'true')
		review_log_form = Review_Log_Form(review_log_root, None)

	def add_user(self):
		user_root = Toplevel()
		user_root.attributes('-topmost', 'true')
		user_form = User_Form(user_root, "add")

	def report(self):
		report_root = Toplevel()
		report_root.attributes('-topmost', 'true')
		report_form = Report_Form(report_root)


	def edit_profile(self):
		edit_profile_root = Toplevel()
		edit_profile_root.attributes('-topmost', 'true')
		profile_form = Profile_Form(edit_profile_root, "edit")

	def add_profile(self):
		add_profile_root = Toplevel()
		add_profile_root.attributes('-topmost', 'true')
		profile_form = Profile_Form(add_profile_root, "add")



class Profile_Form():

	image_list = [] #Array to store file paths of images
	image_list_pointer = -1 #Pointer variable to showing the index of image currently being looked at in the image_list array

	def __init__(self, master, state):
		self.connection = sqlite3.connect('database.db') #Establishes a connection to the database
		self.db = self.connection.cursor()

		self.master = master
		self.state = state
		
		self.name = StringVar()
		self.arrive_by = StringVar()
		self.category = StringVar()
		self.category.set(None) #Sets value of the radiobutton so that it is deselected
		self.open_door = IntVar()

		self.details_label_frame = LabelFrame(master, text="Details")
		self.details_label_frame.place(x=15, y=15)

		self.name_label = Label(self.details_label_frame, text="Name:")
		self.arrive_by_label = Label(self.details_label_frame, text="Arrive by:")
		self.category_label = Label(self.details_label_frame, text="Category:")
		self.open_door_label = Label(self.details_label_frame, text="Open door?")
		
		
		self.arrive_by_entry = Entry(self.details_label_frame, textvariable=self.arrive_by, width=30)

		self.friendly_radiobutton = Radiobutton(self.details_label_frame, text="Friendly", variable=self.category, value="Friendly")
		self.dangerous_radiobutton = Radiobutton(self.details_label_frame, text="Dangerous", variable=self.category, value="Dangerous")
		self.open_door_checkbutton = Checkbutton(self.details_label_frame, variable=self.open_door)
		self.save_button = Button(master, text="Save", width=6, command=lambda: self.save(self.name, self.arrive_by, 
		self.category, self.open_door))

		self.arrive_by_entry.insert(0, "00:00 (24h)") #Inserts correct format of how time should be entered
		self.arrive_by_entry.bind('<FocusIn>', self.on_click_hide) #If the entry field is clicked, the on_click_hide method will run
		self.arrive_by_entry.config(fg="grey") #Makes assistive text grey

		if state == "add":
			master.title("Add Profile")
			self.name_entry = Entry(self.details_label_frame, textvariable=self.name, width=30)
		else:
			master.title("Edit Profile")
			name_list_query = self.db.execute("SELECT Profile_Name FROM Profile") 
			name_list_query = name_list_query.fetchall() #Returns names of profiles in database 

			self.name_list = [] #Defines array to hold the names of profiles
			for name in name_list_query: #Iterates through each tuple in the array
				self.name_list.append(name[0]) #Adds first element of each tuple to the name_list array
			self.name_entry = autocomplete.Auto_Complete_Entry(self.name_list, 30, -2, -18, self.details_label_frame, width=30)
			self.load_button = Button(master, text="Load Profile", width=10, command=lambda: self.load_profile())
			self.load_button.place(x=75, y=220)
			self.delete_button = Button(master, text="Delete Profile", width=10, command=lambda: self.delete_profile())
			self.delete_button.place(x=160, y=220)

		self.name_label.grid(row=0, column=0, padx=(10,10), pady=(10,10))
		self.arrive_by_label.grid(row=1, column=0, padx=(10,10), pady=(10,10))
		self.category_label.grid(row=2, column=0, padx=(10,10), pady=(10,10))
		self.open_door_label.grid(row=3, column=0, padx=(10,10), pady=(10,10))
		self.name_entry.grid(row=0, column=1, columnspan=2, padx=(10,10), pady=(10,10))
		self.arrive_by_entry.grid(row=1, column=1, columnspan=2, padx=(10,10), pady=(10,10))
		self.friendly_radiobutton.grid(row=2, column=1, pady=(10,10))
		self.dangerous_radiobutton.grid(row=2, column=2, pady=(10,10))
		self.open_door_checkbutton.grid(row=3, column=1, padx=(10,10), pady=(10,10))
		self.save_button.place(x=15, y=220)

		self.w = 495
		self.h = 250
		centre(self.w, self.h, master)


		self.image_label_frame = LabelFrame(master, width=160, height=183)  
		self.image_label_frame.place(x=320, y=23)
		self.image_frame = Label(self.image_label_frame, padx=75, pady=79)
		self.image_frame.pack()
		self.move_right_button = Button(master, text=">", width = 4, command=lambda: self.update_image_frame(1))
		self.move_left_button = Button(master, text="<", width = 4, command=lambda: self.update_image_frame(-1))
		self.upload_image_button = Button(master, text="Upload image(s)", width = 15, command=lambda: self.upload_image())
		self.move_right_button.place(x=435, y=220)
		self.move_left_button.place(x=390, y=220)
		self.upload_image_button.place(x=260, y=220)


	def delete_profile(self):
		name = self.name_entry.get().lower() #Retrieves name from entry field
		self.load_profile() #Loads profile details into form
		if name in self.name_list: #Checks whether the name exists in the database
			#Makes sure user wants to delete profile 
			decision = messagebox.askquestion('Delete Profile','Are you sure you want to delete the profile',icon = 'warning')
			if decision == "yes":
				profile_id = self.db.execute("SELECT Profile_Id FROM Profile WHERE Profile_Name = ?", (name,))
				profile_id = profile_id.fetchall()[0][0] #Fetches profile's profile_id

				log_id_list = self.db.execute("SELECT Log_Id FROM Log WHERE Log_ProfileId = ?", (profile_id,))
				log_id_list = log_id_list.fetchall() #Fetches list of log_id's which relate to the profile going to be deleted

				shutil.rmtree("profiles/"+name) #Deletes folder containing profiles images
				for video in log_id_list: #Iterates through each log_id
					video_id = str(video[0]) #Extracts video_id from tuple and converts it to a string
					os.remove("videos/"+video_id+".mp4") #Deletes video from the video sub folder

				self.db.execute("DELETE from Profile where Profile_Name = ?", (name,))
				self.connection.commit() #Deletes profile from database
				
				self.db.execute("DELETE from Log where Log_ProfileId = ?", (profile_id,))
				self.connection.commit() #Deletes logs relating to the profile

				messagebox.showinfo("","Profile deleted")
				self.master.destroy()

				

				



	def load_profile(self):
		name = self.name_entry.get().lower() #Retrieves name from entry field
		if name not in self.name_list: #Checks whether the name exists in the database
			messagebox.showerror("","Profile not found") 
		else:
			details = self.db.execute("SELECT * FROM Profile WHERE Profile_Name = ?", (name,)) #Fetches details of profile from database
			details = details.fetchall()[0] #Returns details of profile 
			self.name_entry.configure(state="disabled") #Prevets the name entry field from being edited
			if details[3] != None: #If there is a arrive_by time for the profile
				self.arrive_by_entry.delete(0, END) #Deletes current contents of the field
				self.arrive_by_entry.config(fg='black') #Changes colour of font to black
				arrive_by_time = datetime.strptime(details[3], '%H:%M:%S') #Converts string time in database to datetime object
				arrive_by_time = datetime.strftime(arrive_by_time, '%H:%M') #Extracts the hours and minutes from datetime object
				self.arrive_by_entry.insert(0, arrive_by_time) #Inserts arrive by time from database into the field
			if details[2] == "friendly": #If category is 'friendly'
					self.category.set("Friendly") #Selects the freindly radiobutton
			else:
				self.category.set("Dangerous") #Select the dangerous radiobutton
			self.open_door.set(details[4]) #Sets open_door checkbox to value in database

			for file in os.listdir('./profiles/'+name): #Iterates through each file in the profile's folder
				image_name, ext = os.path.splitext(file) #Splits the fille path into its name and file extension
				if ext == '.jpg' or ext == '.png' or ext == '.jpeg': #Checks whether extension relates to an image file
					self.image_list.append('./profiles/'+name+'/'+file) #If file is an image, adds it to the image_list
			self.image_list_pointer = 0 #Updates image pointer to point at first image in list
			self.update_image_frame(0) #Updates the image_frame to insert these images 


		 

	def upload_image(self):
		image_directory = filedialog.askopenfilename(initialdir = "/", title = "Select image", filetypes=
		(("png files","*.png"), ("jpg files","*.jpg"), ("jpeg files","*.jpeg"), ("all files","*.*")))
		if image_directory != "": #If a file was selected 
			self.image_list.append(image_directory) #Adds selected file path to the array
			self.image_list_pointer = len(self.image_list)-1 #Changes pointer to point at the image that has just been uploaded
			self.update_image_frame(0) #Displays the image that was just uploaded

	def update_image_frame(self, move):
		if self.image_list_pointer + move <0 or self.image_list_pointer + move > len(self.image_list)-1:
			pass #Means the pointer is at beginning or the end of the array so cannot move further outwards
		else:
			self.image_list_pointer += move #Updates pointer variable

		if len(self.image_list) != 0:
			image_directory = self.image_list[self.image_list_pointer] #Gets file path that pointer currently points to
			pillow_img = Image.open(image_directory) #Opens image with pillow module
			pillow_img = pillow_img.resize((160,175))  #Resizes image to fit the frame
			tk_img = ImageTk.PhotoImage(image=pillow_img, master=self.image_frame) #Converts image to PhotoImage object
			self.image_frame.config(image=tk_img) #Places image inside label
			self.image_frame.image = tk_img


	def on_click_hide(self, event):
 		if self.arrive_by_entry.get() == "00:00 (24h)": #Will only delete contents first time box is clicked
 			self.arrive_by_entry.delete(0, "end") #Deletes contents of the entry field
 			self.arrive_by_entry.insert(0, '') #Inserts empty space for user input
 			self.arrive_by_entry.config(fg='black') #Changes user input to black colour

	def save(self, name, arrive_by, category, open_door):
		
		#Retrieves all the data from the form
		name = self.name_entry.get().lower()
		arrive_by = self.arrive_by.get()
		category = self.category.get().lower()
		open_door = self.open_door.get()
		time_valid = True #Boolean variable to represent whether the time is in the correct format


		if arrive_by != "00:00 (24h)" and arrive_by != "": #Checks if default entry for arrive_by field was changed
			try: #If time has been entered, format needs to be checked
				arrive_by = datetime.strptime(arrive_by, '%H:%M').time() #Tries to convert user entered arrive_by time to datetime object
				arrive_by = str(arrive_by) #Converts time from datetime objet to string object 
			except:
				time_valid = False #If error in converting to specified format, boolean variable becomes False
		else:
			arrive_by = None #If default entry was not changed, then arrive_by time should be empty


		#Fetches record of profile with name same as the one just entered in the form
		name_list = self.db.execute("SELECT * FROM Profile WHERE Profile_Name=?", (name,)) 
		name_list = name_list.fetchall()
		if len(name) < 2: #Checks if name entry is 2 or fewer characters long
			messagebox.showerror("","Please enter a valid name", parent=self.master)
		elif len(name_list) != 0 and self.state == "add": #If name already exists in the database
			messagebox.showerror("","The name you entered already exists, \n please enter a different name", parent=self.master)
		elif time_valid == False: #If time was entered but in wrong format
			messagebox.showerror("","Please enter a valid 24 hour time like this: 21:34", parent=self.master)
		elif category == "None" : #If no category was selected
			messagebox.showerror("","Please select a category", parent=self.master)
		elif len(self.image_list) == 0: #If no images have been uploaded
			messagebox.showerror("","Please upload at least one image", parent=self.master)
		else:
			if self.state == "add":
				sql = ("INSERT INTO Profile (Profile_Name, Profile_Category, Profile_DetectTime, Profile_OpenDoor) Values (?, ?, ?, ?)")
				values =  (name, category, arrive_by, open_door) #Defines variables to be subsituted in as parameters
				self.db.execute(sql, values) 
				os.mkdir("profiles/"+name) #Creates folder for new profile
			else:
				self.db.execute("UPDATE Profile SET Profile_Category = ?, Profile_DetectTime = ?, Profile_OpenDoor = ? WHERE Profile_Name = ?", 
				(category, arrive_by, open_door, name,)) #Updates profiles record in the database
			self.connection.commit()			
			self.connection.close()
			messagebox.showinfo("","Profile saved")
			
			
			for image in self.image_list: #Iterates through each uploaded image
				try: #If image is already in the folder, an error will be raised
					copyfile(image, "profiles/"+name+"/"+os.path.basename(image)) #Copies each image into the new folder
				except:
					pass
			self.master.destroy()
			

class Report_Form():
	result_list = []

	def __init__(self, master):
		self.connection = sqlite3.connect('database.db') #Establishes a connection to the database
		self.db = self.connection.cursor()

		
		self.master = master
		self.master.title("Report")

		self.search_criteria_frame = Frame(master, width=750) #Will contain the search parameters for the user to search using
		self.search_criteria_frame.grid(row=0, column=0)
		self.header_frame = Frame(master, width=750) #Will contain the headings of each column of the report
		self.header_frame.grid(row=1, column=0)
		self.results_frame = Frame(master, width=770) #Will contain the results of the search
		self.results_frame.grid(row=2, column=0)
		self.results_canvas = Canvas(self.results_frame, width=770) #Canvas needed to be able to scroll up/down the frame
		self.results_main_frame = Frame(self.results_canvas, width=770) #Frame to contain the scrollable canvas
		self.buttons_frame = Frame(master, width=200) #Frame to contain the buttons at the bottom of the window 
		self.buttons_frame.grid(row=3, column=0)


		self.results_canvas.create_window((0,0), window=self.results_main_frame, anchor='nw') #Creates window for canvas
		self.results_canvas.pack(side="left")
		self.results_main_frame.bind_all("<MouseWheel>", self.on_mousewheel) #Binds mousewheel action to scroll up/down

		self.scrollbar = Scrollbar(master, orient="vertical", command = self.results_canvas.yview) #Adds a scrollbar to the results_canvas
		self.scrollbar.grid(row=2, column=1, sticky="nsew")
		self.results_canvas['yscrollcommand'] = self.scrollbar.set #Sets scrollbar to scroll the results_canvas

		name_list_query = self.db.execute("SELECT Profile_Name FROM Profile") 
		name_list_query = name_list_query.fetchall() #Returns names of profiles in database 

		self.database_name_list = [] #Defines array to hold the names of profiles
		for name in name_list_query: #Iterates through each tuple in the array
		   self.database_name_list.append(name[0]) #Adds first element of each tuple to the name_list array

		self.photo = PhotoImage(file="calendar.png") #Loads image of calendar 
		self.calendar_image = self.photo.subsample(40,40) #Resizes images 

		self.log_id = StringVar() #Variable to store log id
		self.profile_id = StringVar() #Variale to store profile id
		self.date_1 = StringVar() #Variable to store the beginning date of the date range
		self.date_2 = StringVar() #Variable to store the end date of the date range

		self.log_id_label = Label(self.search_criteria_frame, text="Log Id:")
		self.date_label = Label(self.search_criteria_frame, text="Date:")
		self.profile_id_label = Label(self.search_criteria_frame, text="Profile Id:")		
		self.to_label = Label(self.search_criteria_frame, text="to")
		self.name_label = Label(self.search_criteria_frame, text="Name:")
	
		self.log_id_entry = Entry(self.search_criteria_frame, textvariable=self.log_id, width=15)
		self.profile_id_entry = Entry(self.search_criteria_frame, textvariable=self.profile_id, width=15)
		self.date_1_entry = Entry(self.search_criteria_frame, textvariable=self.date_1, width=15)
		self.date_2_entry = Entry(self.search_criteria_frame, textvariable=self.date_2, width=15)
		self.name_entry = autocomplete.Auto_Complete_Entry(self.database_name_list, 15, 0, 0, self.search_criteria_frame, width=15)


		#defines the calendar buttons which will open up a calendar when clicked
		self.calendar_button_1 = Button(self.search_criteria_frame, borderwidth=1, height=17, width=17, command = 
		lambda: datepicker.MyDatePicker(format_str='%02d/%s/%s', entry=self.date_1_entry))
		self.calendar_button_2 = Button(self.search_criteria_frame, borderwidth=1, height=17, width=17, command = 
		lambda: datepicker.MyDatePicker(format_str='%02d/%s/%s', entry=self.date_2_entry))
		self.search_button = Button(self.search_criteria_frame, text="Search", width=12, command = lambda:self.search())       
		self.calendar_button_1.config(image=self.calendar_image) #Adds image of calendar to button
		self.calendar_button_2.config(image=self.calendar_image)

		self.log_id_label.grid(row=0, column=0, padx=(0,0), pady=(30,10))
		self.profile_id_label.grid(row=1, column=0, padx=(10,10), pady=(10,10))
		self.date_label.grid(row=1, column=2, padx=(40,10), pady=(10,10))
		self.to_label.grid(row=1, column=5, padx=(5,0), pady=(10,10))
		self.name_label.grid(row=0, column=2, padx=(40,10), pady=(30,10))

		self.log_id_entry.grid(row=0, column=1, padx=(10,10), pady=(30,10))
		self.profile_id_entry.grid(row=1, column=1, padx=(10,10), pady=(10,10))
		self.date_1_entry.grid(row=1, column=3, padx=(0,0), pady=(10,10))
		self.date_2_entry.grid(row=1, column=6, padx=(5,0), pady=(10,10))
		self.name_entry.grid(row=0, column=3, pady=(30,10))

		self.calendar_button_1.grid(row=1, column=4, pady=(0,0), sticky=W)
		self.calendar_button_2.grid(row=1, column=7, pady=(0,0), sticky=W)
		self.search_button.grid(row=0, column=4, columnspan=4, padx=(40,0), pady=(30,10))

		log_id_label = Label(self.header_frame, text="Log Id: ")
		log_id_label.grid(sticky=NSEW, row=0, column=0, padx=(35,35), pady=5)
		date_label = Label(self.header_frame, text="Date: ")
		date_label.grid(sticky=NSEW, row=0, column=1, padx=(35,35), pady=5)
		profile_id_label = Label(self.header_frame, text="Profile Id: ")
		profile_id_label.grid(sticky=NSEW, row=0, column=3, padx=(35,35), pady=5)
		name_label = Label(self.header_frame, text="Name: ")
		name_label.grid(sticky=NSEW, row=0, column=4, padx=(35,35), pady=10)
		enter_time_label = Label(self.header_frame, text="Enter Time: ")
		enter_time_label.grid(sticky=NSEW, row=0, column=5, padx=(35,35), pady=5)
		exit_time_label = Label(self.header_frame, text="Exit Time: ")
		exit_time_label.grid(sticky=NSEW, row=0, column=6, padx=(35,35), pady=5)
	
		self.create_record_row(30)		

		self.clear_button = Button(self.buttons_frame, text="Clear", width=12, command = lambda:self.clear()) 
		self.export_button = Button(self.buttons_frame, text="Export", width=12, command = lambda:self.export())
		self.clear_button.grid(row=0, column=0, padx=(500,0), pady=(20,0))
		self.export_button.grid(row=0, column=1, padx=(30,0), pady=(20,0))

		self.w = 800
		self.h = 510
		centre(self.w, self.h, master) #Centres window

	def create_record_row(self, number_of_rows):
		self.log_id_list = []
		self.date_list = []
		self.profile_id_list = []
		self.name_list = []
		self.enter_time_list = []
		self.exit_time_list = []
		self.view_log_button_list = []

		#Deletes the results table
		for widget in self.results_main_frame.winfo_children():
			widget.destroy()


		photo = PhotoImage(file="arrow.png") #Loads image of arrow 
		arrow_image = photo.subsample(40,40) #Resizes image 

		if number_of_rows < 15: #If there are less than 15 search results
			number_of_rows = 15 #Minimum number of rows on the winow
		h = 300 #Height of canvas to accomodate minimum of 15 rows, others will be scrollable
		#Configures canvas height so it scrolls when number of rows exceeds 15
		self.results_main_frame.bind("<Configure>", lambda event:self.set_scroll(event,h)) 

		for row in range(0, number_of_rows):
			self.log_id_result = StringVar() #All the results will be string variables
			self.log_id_result = Entry(self.results_main_frame)
			self.log_id_result.grid(row=row, column=0)
			self.log_id_list.append(self.log_id_result) #Adds the entry object to the corresponding array

			self.date_result = StringVar()
			self.date_result = Entry(self.results_main_frame)
			self.date_result.grid(row=row, column=1)
			self.date_list.append(self.date_result)


			self.profile_id_result = StringVar()
			self.profile_id_result = Entry(self.results_main_frame)
			self.profile_id_result.grid(row=row, column=2)
			self.profile_id_list.append(self.profile_id_result)

			self.name_result = StringVar()
			self.name_result = Entry(self.results_main_frame)
			self.name_result.grid(row=row, column=3)
			self.name_list.append(self.name_result)

			self.enter_time_result = StringVar()
			self.enter_time_result = Entry(self.results_main_frame)
			self.enter_time_result.grid(row=row, column=4)
			self.enter_time_list.append(self.enter_time_result)

			self.exit_time_result = StringVar()
			self.exit_time_result = Entry(self.results_main_frame)
			self.exit_time_result.grid(row=row, column=5)
			self.exit_time_list.append(self.exit_time_result)

			self.view_log_button = Button(self.results_main_frame, height=16, width=16, borderwidth=1, command=lambda c=row:Thread(target=self.view_log(c)).start())
			self.view_log_button.config(image=arrow_image) #Adds reference to image so the button will contain the image of the arrow
			self.view_log_button.image = arrow_image
			self.view_log_button.grid(row=row, column=6, padx=(2,0))
			self.view_log_button_list.append(self.view_log_button)


	def clear(self):
		self.create_record_row(15) #Deletes current table and creates new one
		#Deletes all search criteria entries
		self.log_id_entry.delete(0, END)
		self.profile_id_entry.delete(0, END)
		self.name_entry.delete(0, END)
		self.date_1_entry.delete(0, END)
		self.date_2_entry.delete(0, END)
		self.result_list = []
        
	def export(self):
		#Defines new workbook
		wb = Workbook() 
		sheet1 = wb.add_sheet('Report') 

		#Inserts the column text 
		sheet1.write(0, 0, 'Log Id:') 
		sheet1.write(0, 1, 'Date:') 
		sheet1.write(0, 2, 'Profile Id:') 
		sheet1.write(0, 3, 'Name:') 
		sheet1.write(0, 4, 'Enter Time:') 
		sheet1.write(0, 5, 'Exit Time:') 

		if len(self.result_list) == 0: #If no records to export
			messagebox.showinfo("No data to export", "No data to export")
		else:
			#Asks user for location to save the file to
			directory = filedialog.asksaveasfilename(defaultextension = "xls")
			#If no directory has been chosen
			if directory == "":
				pass
			else:
				number_of_record = len(self.result_list)/6 #Calculates number of rows 
				for i in range(0,int(number_of_record)): #Iterates through each row
					for column in range(0,6): #Iterates through each cell in each row
							sheet1.write(i+1, column, self.result_list[i*6+column])#Inserts data into the cell
				wb.save(directory) #Saves the workbook to the pre-selected directory


	def view_log(self, row):
		if len(self.result_list) != 0:
			review_log_root = Toplevel()
			review_log_root.attributes('-topmost', 'true')
			review_log_form = Review_Log_Form(review_log_root, self.result_list[row*6])
		else:
			pass


	def set_scroll(self,event,h):
		self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"),width=770,height=h)

	def on_mousewheel(self, event):
		shift = (event.state & 0x1) != 0 #If mousewheel has been moved in x direction stores True
		scroll = -1 if event.delta > 0 else 1 #Gets by how many scrolls shifter has moved
		if shift: 
			self.results_canvas.xview_scroll(scroll, "units") 
		else:
			self.results_canvas.yview_scroll(scroll, "units")

	def search(self):
		#Retrieves data from report form
		log_id = self.log_id.get()
		profile_id = self.profile_id.get()
		date_1 = self.date_1.get()
		date_2 = self.date_2.get()
		name = self.name_entry.get().lower()

		#Sets boolean variables relating to the validity of the parameters they have entered
		log_id_valid = True
		profile_id_valid = True

		query = ("SELECT Log_Id, Log_Date, Log_ProfileId, Log_StartTime, Log_EndTime FROM Log ") #Defines the most basic query that will be used if no parameters are entere
		variable = () #Defines a  tuple to hold the variables that will be passed to the query
		#If a log id has been entered, it will be searched for
		if log_id != "": #Checks if a log id has been entered
			try:
				log_id = int(log_id) #Tests whether input is an integer
			except:
				log_id_valid = False
				messagebox.showerror("","Please enter a valid log id")
			if log_id_valid == True: #If the log id is an integer
				query = query + ("WHERE Log_Id=? ") #Adds to the query
				variable = variable + (log_id,)
		#If no log id has been entered, the search will be based off the profile id
		elif profile_id != "": #Checks whether a profile id has been entered 
			try:
				profile_id = int(profile_id) #Tests whether input is an integer
			except:
				profile_id_valid = False
				messagebox.showerror("","Please enter a valid profile id")
			if profile_id_valid == True: #If profile id is an integer
				query = query + ("WHERE Log_ProfileId=? ")
				variable = variable + (profile_id,)
		elif name != "":
			#Checks if name exists in database
			if name not in self.database_name_list:
				messagebox.showerror("","Profile with name entered does not exist")
			else:
				#Retrieves profile id for the name entered
				profile_id = self.db.execute("SELECT Profile_Id FROM Profile WHERE Profile_Name =?", (name,))
				profile_id = profile_id.fetchall()[0][0]
				query = query + ("WHERE Log_ProfileId=? ") 
				variable = variable + (profile_id, )


		if date_1 == "" and date_2 == "": #If both date fields are empty
			pass #The query does not change
		else:
			date_1_valid, date_1 = self.validate_date(date_1)
			date_2_valid, date_2 = self.validate_date(date_2)
			#If atleast one of the dates is valid and the original query has not been changed
			if (date_1_valid == True or date_2_valid == True) and len(query) == 76:
				query = query + ("WHERE ") #'Where' is added for the date parameters if no parameters have already been added
			elif date_1_valid == True or date_2_valid == True: #If only one of the dates are valid
				query = query + ("AND ") #If there is also a parameter, 'and' is concatenated
			#If both dates are valid
			if date_1_valid == True and date_2_valid == True: 
				query = query + ("Log_Date BETWEEN ? AND ? ") #Search for records between these dates
				variable = variable + (date_1, date_2, )
			elif date_1_valid == True: #If only beginning date is valid
				query = query + ("Log_Date >=? ") #Search for records from that date
				variable = variable + (date_1, )
			elif date_2_valid == True: #If only end date is valid
				query = query + ("Log_Date <=? ") #Search for records upto second date
				variable = variable + (date_2, )
			else:
				#If date fields are not empty and entries are not valid dates, error message is shown
				messagebox.showerror("","Please enter a valid date")
		query = query + ("ORDER BY Log_Date ASC") #Orders results by date in ascending order
		log_result_list_raw = self.db.execute(query, variable)
		log_result_list_raw = log_result_list_raw.fetchall() #Fetches records relating to search parameters
		if len(log_result_list_raw) == 0: #If no records match the criteria
			messagebox.showinfo("", "No logs found")
			self.result_list = []
			self.create_record_row(15)
		else:
			log_result_list = [] #Array to hold each element from the search results
			#Turns the array of tuples into a 1D array which is easier to work with
			for record in log_result_list_raw: #Iterates through each tuple
				position = 0
				for element in record: #Iterates through each element in each tuple
					if position == 1: #If element is the date
						date = datetime.strptime(element, "%Y-%m-%d").strftime("%d/%m/%Y") #Formats date
						log_result_list.append(date)
					elif position == 2: #If the element is the profile id
						#Fetches the name of the profile
						profile_name = self.db.execute("SELECT Profile_Name FROM Profile WHERE Profile_Id = ?", (element,))
						profile_name = profile_name.fetchall()[0][0]
						log_result_list.append(element) #Adds the profile id to the array
						log_result_list.append(profile_name) #Adds the profile name to the array
					elif element is None: #If field contains Null value
						log_result_list.append("")
					else:
						log_result_list.append(element) #Adds the element in the tuple to the array
					position = position + 1
			self.result_list = log_result_list
			
			self.populate_results_table(log_result_list)

	def populate_results_table(self, result_list):
		self.create_record_row(int(len(result_list)/6)) #Creates extra rows in case more than 15 records need to be displayed
		#Defines two arrays, widgets holds the name of the widget and entries hold each entry object
		widgets = [self.log_id_result, self.date_result, self.profile_id_result, self.name_result, self.enter_time_result, self.exit_time_result]
		entries = [self.log_id_list, self.date_list, self.profile_id_list, self.name_list, self.enter_time_list, self.exit_time_list]
		
		#Inserts records into the table
		widget_counter = 0 
		#Iterates through each widget 
		for widget in widgets:
			row_counter = 0
			#Iterates through each cell in each column
			for entry in entries[widget_counter]:
				#If index is out of range
				if row_counter*6 + widget_counter > len(result_list)-1:
					pass
				else:
					#Inserts data into the cell
					entry.insert(END, result_list[row_counter*6 + widget_counter])
				row_counter = row_counter + 1 
			widget_counter = widget_counter + 1



	def validate_date(self, date):
		valid = True
		if date == "":
			valid = ("Empty")
		else:
			try:
				#Tries to convert date to the format needed for it to be used in the query
				date = datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")
			except:
				valid = False
		return(valid, date)

 

class Review_Log_Form():

	def __init__(self, master, required_log_id):
		print(required_log_id)
		self.connection = sqlite3.connect('database.db') #Establishes a connection to the database
		self.db = self.connection.cursor()

		name_list_query = self.db.execute("SELECT Profile_Name FROM Profile") 
		name_list_query = name_list_query.fetchall() #Returns names of profiles in database 
		self.database_name_list = [] #Defines array to hold the names of profiles
		for name in name_list_query: #Iterates through each tuple in the array
		   self.database_name_list.append(name[0]) #Adds first element of each tuple to the name_list array

		self.master = master
		self.master.title("Review Log")
		self.required_log_id = required_log_id

		self.log_id = StringVar()
		self.date = StringVar()
		self.enter_time = StringVar()
		self.exit_time = StringVar()
		self.name = StringVar()

		self.log_id_label = Label(master, text="Log Id:")
		self.date_label = Label(master, text="Date:")
		self.enter_time_label = Label(master, text="Enter Time:")
		self.exit_time_label = Label(master, text="Exit time:")
		self.text_label = Label(master, text="Is this correct?\n If not please select the correct profile")
		self.name_label = Label(master, text="Name:")
		self.log_id_entry = Entry(master, textvariable=self.log_id, width=15)
		self.date_entry = Entry(master, textvariable=self.date, width=15)
		self.enter_time_entry = Entry(master, textvariable=self.enter_time, width=15)
		self.exit_time_entry = Entry(master, textvariable=self.exit_time, width=15)
		self.name_entry = autocomplete.Auto_Complete_Entry(self.database_name_list, 15, 0, 0, master, width=15)
		self.save_button = Button(master, text="Save", command=lambda:self.save(), width=15)

		self.log_id_label.grid(row=0, column=0, padx=(30,30), pady=(20,10))
		self.log_id_entry.grid(row=0, column=1, padx=(0,20), pady=(20,10))
		self.date_label.grid(row=1, column=0, padx=(30,30), pady=(0,10))
		self.date_entry.grid(row=1, column=1, padx=(0,20), pady=(0,10))
		self.enter_time_label.grid(row=2, column=0, padx=(30,30), pady=(0,10))
		self.enter_time_entry.grid(row=2, column=1, padx=(0,20), pady=(0,10))
		self.exit_time_label.grid(row=3, column=0, padx=(30,30), pady=(0,10))
		self.exit_time_entry.grid(row=3, column=1, padx=(0,20), pady=(0,10))
		self.text_label.grid(row=1, column=2, columnspan=2, padx=(0,30))
		self.name_label.grid(row=2, column=2, padx=(20,0))
		self.name_entry.grid(row=2, column=3, padx=(0,70))
		self.save_button.grid(row=3, column=3, padx=(0,100))

		self.image_label_frame = LabelFrame(master, width=160, height=183)  
		self.image_label_frame.grid(row=4, column=3, padx=(20,50), pady=(30,0))
		self.image_frame = Label(self.image_label_frame, padx=75, pady=79)
		self.image_frame.pack()
		self.move_right_button = Button(master, text=">", width = 4, command=lambda: self.update_image_frame(1))
		self.move_left_button = Button(master, text="<", width = 4, command=lambda: self.update_image_frame(-1))	
		self.move_right_button.place(x=465, y=380)
		self.move_left_button.place(x=420, y=380)

		self.video_label_frame = LabelFrame(master, width=360, height=183)  
		self.video_label_frame.grid(row=4, column=0, columnspan=3, padx=(30,0), pady=(30,0))
		self.video_frame = Label(self.video_label_frame, padx=150, pady=79)
		self.video_frame.pack()
		self.play_button = Button(master, text="Play/Pause", width=10, command=lambda: self.play_video())
		self.play_button.place(x=150, y=380)	

		self.w = 550
		self.h = 420
		centre(self.w, self.h, master) #Centres window


		self.photo = PhotoImage(file="bin.png") #Loads image of bin 
		self.bin_image = self.photo.subsample(28,28) #Resizes image
		self.delete_button = Button(master, command=lambda:self.delete_image(), width=20, height=20)
		self.delete_button.config(image=self.bin_image)
		self.delete_button.place(x=380, y=380)

		self.next_log_id()

		
	def next_log_id(self):
		self.unreviewed_log_id_list = [] #Array to hold log id's which have not been reviewed
		if self.required_log_id is None: #If log id has not been passed as a parameter
			#Retrieves log id's which have not been reviewed
			unreviewed_log_id_query = self.db.execute("SELECT Log_Id FROM Log WHERE Log_FaceReview=? ORDER BY Log_Id ASC ", (0,))
			unreviewed_log_id_query = unreviewed_log_id_query.fetchall()
			#Converts the array of tuples into an array 
			if len(unreviewed_log_id_query) != 0:
				for log_id in unreviewed_log_id_query:
					self.unreviewed_log_id_list.append(log_id[0])
				self.required_log_id = self.unreviewed_log_id_list[0] #Gets the log id of the log to be reviewed next
				self.unreviewed_log_id_list.pop() #Removes the log id that has just been selected to be reviewed
				self.populate_form() #Populates form
			else:
				messagebox.showerror("","There are no logs to review", parent=self.master)
				self.master.destroy()
			 

	def populate_form(self):
		#Defines boolean variables to contain the current state of the video
		self.play = True
		self.pause = False	
		self.name_entry.focus() #Places cursor on the name entry field 

		log_details = self.db.execute("SELECT Log_Date, Log_ProfileId, Log_StartTime, Log_EndTime FROM Log WHERE Log_Id=?", (self.required_log_id,))
		log_details = log_details.fetchall() #Fetched log details
		self.log_details = log_details
		date = log_details[0][0] #Extracts date
		date = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y") #Converts date to required format
		#Inserts log id, date and entry time
		self.log_id_entry.insert(0, self.required_log_id)
		self.date_entry.insert(0, date)
		self.enter_time_entry.insert(0, log_details[0][2])
		#Checks if exit time is not Null, if exit time is Null, entry box is left empty
		if log_details[0][3] is not None:
			self.exit_time_entry.insert(0, log_details[0][3])
		#Fetches corresponding profile name for the log
		self.name = self.db.execute("SELECT Profile_Name From Profile WHERE Profile_Id=?", ((log_details[0][1]),))
		self.name = self.name.fetchall()[0][0]
		self.name_entry.insert(0, self.name)

		#Makes all entry boxes read only
		self.log_id_entry.config(state="disabled")
		self.date_entry.config(state="disabled")
		self.enter_time_entry.config(state="disabled")
		self.exit_time_entry.config(state="disabled")

		#Fetches video of the log
		self.cap = cv2.VideoCapture("videos/"+str(self.required_log_id)+".mp4") #Defines connection between the program and the camera
		self.face_classifier = cv2.CascadeClassifier('haarcascade_frontalface_default.xml') #Loads haarcascade into the program
		self.face_counter = 0 #Variable to store number of face images that have been extracted
		self.face_image_list = [] #Array to store the images of the faces
		self.image_list_pointer = 0 #Pointer variable to point to the current image displayed on the screen
		#Displays images of the face 
		self.extract_face()

		#Displays the video
		self.show_frame()
		self.play_video() 

	def save(self):
		name = self.name_entry.get() #Retrieves name
		if name not in self.database_name_list: #If name is not valid
			messagebox.showerror("","Please enter a valid name")
		else: 
			#Fetches profile id for name entered by the user
			profile_id = self.db.execute("SELECT Profile_Id FROM Profile WHERE Profile_Name=?", (name, ))
			profile_id = profile_id.fetchall()[0][0]
			#Updates record in database log table with new profile id and sets Log_FaceReview to 1 
			self.db.execute("UPDATE Log set Log_ProfileId=?, Log_FaceReview=? WHERE Log_Id=?", (profile_id, 1 , self.required_log_id,))
			self.connection.commit()

			for face in self.face_image_list: #Iterates through each uploaded image
				face = cv2.cvtColor(face, cv2.COLOR_RGBA2BGRA) #Converts colour format
				#Gives each image a unique name based on the date and time
				image_name = str(datetime.now().date()) + '_' + str(datetime.now().time()).replace(':', '.')
				cv2.imwrite("profiles/"+name+"/"+image_name+".png", face) #Saves image to the correct folder
			messagebox.showinfo("","The log has been successfully reviewed", parent = self.master)
			if len(self.unreviewed_log_id_list) != 0: #If log id has not been specified
				self.clear() 
				self.required_log_id = None
				self.next_log_id()
			else:
				self.master.destroy()


	def clear(self):
		#Changes state of entry fields so their contents can be deleted
		self.log_id_entry.config(state="normal") 
		self.date_entry.config(state="normal")
		self.enter_time_entry.config(state="normal")
		self.exit_time_entry.config(state="normal")
		#Deletes contents of all entry boes
		self.log_id_entry.delete(0, END)
		self.date_entry.delete(0, END)
		self.enter_time_entry.delete(0, END)
		self.exit_time_entry.delete(0, END)
		self.name_entry.delete(0, END)
		#Makes the video and image frames empty
		self.image_frame.config(image="")
		self.video_frame.config(image="")	



	def delete_image(self):
		if len(self.face_image_list) != 0: #If there are still images in the array
			self.face_image_list.pop(self.image_list_pointer) #Removes image currently being looked at from array
			if self.image_list_pointer == len(self.face_image_list): #If pointer is pointing to last element in array
				self.image_list_pointer = self.image_list_pointer-1 #Decrements pointer variable
			self.update_image_frame(0) #Updates image frame
	



	def play_video(self):
		if self.pause == True: #If video is currently playing
			self.pause = False
			self.play = True
		else:						  #If video has been paused
			self.play = False
			self.pause = True

	def face_extractor(self, frame):
		faces = self.face_classifier.detectMultiScale(frame, 1.3, 5)#Detects faces if any present in the frame

		if faces is (): #If no faces have been detected
			return None

		# Crop all faces found
		for (x,y,w,h) in faces:
			cropped_face = frame[y:y+h+50, x:x+w+50] #Crops image 
		return cropped_face

	

	def extract_face(self):
		ret, frame =self.cap.read()
		face_extract = self.face_extractor(frame) #Determines whether a face is present
		if face_extract is not None: #If a face is present
			try:
				face = cv2.resize(face_extract, (400, 400)) #Resizes image of face 
				face = cv2.cvtColor(face_extract, cv2.COLOR_RGBA2BGRA) #Converts colour format
				self.face_image_list.append(face)#Adds the face to the array
				self.update_image_frame(0) #Updates the window with the new image
				self.face_counter = self.face_counter + 1 #Increments face counter
			except:
				pass
		if self.face_counter<5: #If less than 5 faces have been found
			self.image_frame.after(1, self.extract_face) #Executes show_frame method every 10 milliseconds
		else: #If 5 images have been detected
			self.cap.release()




	def show_frame(self):	
		if self.play == True:
			try:
				ret, frame = self.cap.read() #Reads frame from camera
				cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA) #Converts frame to BGR from RGBA
				img = Image.fromarray(cv2_image) #Converts frame to Image object
				img = img.resize((300, 183), Image.ANTIALIAS) #Resizes video frame to fit the dashboard window
				imgtk = ImageTk.PhotoImage(image=img) #Converts image 'img' to photoimage so it can be displayed in the window

				self.video_frame.imgtk = imgtk
				self.video_frame.configure(image=imgtk)
			except:
				pass
			if ret == False: #If at the end of the video
				self.cap = cv2.VideoCapture("videos/"+str(self.required_log_id)+".mp4") #Redefines cap variable so video restarts
		self.video_frame.after(100, self.show_frame) #Executes show_frame method every 10 milliseconds


	def update_image_frame(self, move):
		if self.image_list_pointer + move <0 or self.image_list_pointer + move > len(self.face_image_list)-1:
			pass #Means the pointer is at beginning or the end of the array so cannot move further outwards
		else:
			self.image_list_pointer += move #Updates pointer variable

		if len(self.face_image_list) != 0:
			face = self.face_image_list[self.image_list_pointer] #Gets file path that pointer currently points to
			pillow_img = Image.fromarray(face) #Opens image with pillow module
			pillow_img = pillow_img.resize((160,183))  #Resizes image to fit the frame
			tk_img = ImageTk.PhotoImage(image=pillow_img, master=self.image_frame) #Converts image to PhotoImage object
			self.image_frame.config(image=tk_img) #Places image inside label
			self.image_frame.image = tk_img
		else:
			self.image_frame.config(image="")

class User_Form():

	def __init__(self, master, state):
		self.connection = sqlite3.connect('database.db') #Establishes a connection to the database
		self.db = self.connection.cursor()
		#Defines variables to store user inputs 
		self.username = StringVar()
		self.first_name = StringVar()
		self.surname = StringVar()
		self.password = StringVar()
		self.access_level = StringVar()
		self.access_level.set(None)
		self.master = master
		self.state = state #Makes the state an attribute of the class
		self.details_label_frame = LabelFrame(master, text="Details", )
		self.details_label_frame.pack(pady=(10,10))

		#If add user form
		if state == "add":
			master.title("Add User")
			self.username_entry = Entry(self.details_label_frame, textvariable=self.username, width=20)
			self.password_label = Label(self.details_label_frame, text="Password:")
			self.password_entry = Entry(self.details_label_frame, width=20, textvariable=self.password)
			self.password_label.grid(row=0, column=2, padx=(10,10), pady=(10,8))
			self.password_entry.grid(row=0, column=3, columnspan=3, padx=(10,10), pady=(10,8))

			self.save_button = Button(master, width=15, text="Add User", command=lambda:self.save_user())
			self.save_button.pack(padx=(350,0), pady=(2,5))
		else:
			#If edit user form
			master.title("Edit User")
			self.username_list_query = self.db.execute("SELECT User_Login FROM User") 
			self.username_list_query = self.username_list_query.fetchall() #Returns usernames of users in database 
			self.username_list = [] #Defines array to hold the usernames
			for username in self.username_list_query: #Iterates through each tuple in the array
				self.username_list.append(username[0]) #Adds first element of each tuple to the username_list array
			self.username_entry = autocomplete.Auto_Complete_Entry(self.username_list, 20, -2, -18, self.details_label_frame, width=20)
			self.load_user_button = Button(master, width=10, text="Load User", command=lambda:self.load_user())
			self.load_user_button.place(x=15, y=170)
			self.load_user_button = Button(master, width=10, text="Delete User", command=lambda:self.delete_user())
			self.load_user_button.place(x=110, y=170)
			self.save_button = Button(master, width=10, text="Save User", command=lambda:self.save_user())
			self.save_button.place(x=400, y=170)
	

		self.username_label = Label(self.details_label_frame, text="Username:")
		self.first_name_label = Label(self.details_label_frame, text="First name:")
		self.surname_label = Label(self.details_label_frame, text="Surname:")
		self.access_level_label = Label(self.details_label_frame, text="Access Level")		
		self.first_name_entry = Entry(self.details_label_frame, width=20, textvariable=self.first_name)
		self.surname_entry = Entry(self.details_label_frame, width=20, textvariable=self.surname)
		self.camera_radiobutton = Radiobutton(self.details_label_frame, text="Camera", variable=self.access_level, value="0")
		self.report_radiobutton = Radiobutton(self.details_label_frame, text="Report", variable=self.access_level, value="1")
		self.manager_radiobutton = Radiobutton(self.details_label_frame, text="Manager", variable=self.access_level, value="2")
		self.admin_radiobutton = Radiobutton(self.details_label_frame, text="Admin", variable=self.access_level, value="3")
		#Creates help button
		self.photo = PhotoImage(file="help.png") #Loads help icon
		self.photo = self.photo.subsample(120,120) #Resizes image
		self.help_button = Button(self.details_label_frame, command=lambda:self.help_window())
		self.help_button.config(image=self.photo)
		self.username_label.grid(row=0, column=0, padx=(10,10), pady=(10,8))
		self.first_name_label.grid(row=1, column=0, padx=(10,10), pady=(0,8))
		self.surname_label.grid(row=2, column=0, padx=(10,10), pady=(0,30))
		self.access_level_label.grid(row=1, column=2, padx=(10,10), pady=(7,8))
		self.username_entry.grid(row=0, column=1, padx=(10,10), pady=(10,8))
		self.first_name_entry.grid(row=1, column=1, padx=(10,10), pady=(0,8))
		self.surname_entry.grid(row=2, column=1, padx=(10,10), pady=(0,30))
		self.camera_radiobutton.grid(row=1, column=4)
		self.manager_radiobutton.grid(row=2, column=4, pady=(0,30))
		self.report_radiobutton.grid(row=1, column=5)
		self.admin_radiobutton.grid(row=2, column=5, pady=(0,30))
		self.help_button.grid(row=1, column=3, pady=(10,5))

		self.w = 520
		self.h = 210
		centre(self.w, self.h, master)


	def help_window(self):
		window = Toplevel()
		window.title("Access Levels")

		camera_label = Label(window, text="Camera - Only has access to the live stream\n running facial recognition.\n", justify=LEFT)
		camera_label.grid(row=0, column=0, sticky=W)

		report_label = Label(window, text="Report - Can also access reports and past logs.\n", justify=LEFT)
		report_label.grid(row=1, column=0, sticky=W)
     	
		manager_label = Label(window, text="Manager - Can also add/edit access profiles\n and access past detections.\n", justify=LEFT)
		manager_label.grid(row=2, column=0, sticky=W)

		admin_label = Label(window, text="Admin - Has complete access to the whole\nsystem.\n", justify=LEFT)
		admin_label.grid(row=3, column=0, sticky=W)
		width = 250
		height = 180
		centre(width, height, window)

	def delete_user(self):
		username = self.username_entry.get().lower() #Retrieves name from entry field
		if username not in self.username_list: #Checks whether the name exists in the database
			messagebox.showerror("","User does not exist") 
		else:
			decision = messagebox.askquestion('Delete User','Are you sure you want to delete this user',icon = 'warning')
			if decision == "yes":
				self.db.execute("DELETE from User where User_Login = ?", (username,))
				self.connection.commit() #Deletes logs relating to the profile
				messagebox.showinfo("","User deleted", parent=self.master)
				self.username_list.remove(username)
				self.clear()

	def load_user(self):
		username = self.username_entry.get().lower() #Retrieves name from entry field
		if username not in self.username_list: #Checks whether the name exists in the database
			messagebox.showerror("","User does not exist", parent=self.master) 
		else:
			self.clear()
			details = self.db.execute("SELECT * FROM User WHERE User_Login = ?", (username,)) #Fetches details of profile from database
			details = details.fetchall()[0] #Returns details of profile 
			self.username_entry.insert(0, username)
			self.username_entry.configure(state="disabled") #Prevents the name entry field from being edited
			self.first_name_entry.insert(0, details[1])
			self.surname_entry.insert(0, details[2])
			self.access_level.set(details[5])

	def save_user(self):
		#Retrieves details from user form
		username = self.username_entry.get().lower()
		first_name = self.first_name.get().lower()
		surname = self.surname.get().lower()
		password = self.password.get()
		access_level = self.access_level.get()
		if self.state == "add":
			#If adding a user
			username_list_query = self.db.execute("SELECT User_Login FROM User") 
			username_list_query = username_list_query.fetchall() #Returns names of profiles in database 
			database_username_list = [] #Defines array to hold the names of profiles
			for database_username in username_list_query: #Iterates through each tuple in the array
			   database_username_list.append(database_username[0]) #Adds first element of each tuple to the name_list array
			if username == "": #If no username has been entered
				messagebox.showerror("","Please enter a username", parent=self.master)
			elif username in database_username_list: #If username already exists in the database
				messagebox.showerror("","Username already exists", parent=self.master)
			elif first_name == "": #If firstname entry is empty
				messagebox.showerror("","Please enter a first name", parent=self.master)
			elif surname == "": #If surname entry is empty
				messagebox.showerror("", "Please enter a surname", parent=self.master)
			elif len(password) < 7: #If password length is less than 7 characters
				messagebox.showerror("", "Please enter a password with atleast 7 characters", parent=self.master)
			elif access_level == ("None"): #If no access level has been selected 
				messagebox.showerror("", "Please select an access level", parent=self.master)
			else:
				hashed_password = hashlib.sha1(password.encode('utf-8')) #Hashes the password using the SHA1 hashing algorithm
				hashed_password = hashed_password.hexdigest() #Extracts actual digest in hexadecimal form
				insert_user_query = ("INSERT INTO User (User_Login, User_Firstname, User_Surname, User_Password, User_AccessLevel) Values (?, ?, ?, ?, ?)")			
				values =  (username, first_name, surname, hashed_password, access_level)#Defines variables to be subsituted in as parameters
				self.db.execute(insert_user_query, values)
				self.connection.commit()
				messagebox.showinfo("","User added", parent=self.master)
				self.clear() #Clears the add user form 
		else:
			if first_name == "":
				messagebox.showerror("","Please enter a first name", parent=self.master)
			elif surname == "":
				messagebox.showerror("", "Please enter a surname", parent=self.master)
			elif access_level == ("None"):
				messagebox.showerror("", "Please select an access level", parent=self.master)
			else:
				self.db.execute("UPDATE User SET User_Firstname = ?, User_Surname = ?, User_AccessLevel = ? WHERE User_Login = ?", 
				 (first_name, surname, access_level, username,)) #Updates profiles record in the database
				self.connection.commit()
				messagebox.showinfo("","User updated", parent=self.master)
				self.clear()

	def clear(self):
		if self.state == "add":
			self.password_entry.delete(0, END)
		else:
			self.username_entry.config(state="normal")
		self.username_entry.delete(0, END)
		self.first_name_entry.delete(0, END)
		self.surname_entry.delete(0, END)
		self.access_level.set(None)



class Change_Password():

	def __init__(self, master):
		self.master = master
		self.connection = sqlite3.connect('database.db') #Establishes a connection to the database
		self.db = self.connection.cursor()

		self.master.title("Change password")

		self.current_password = StringVar()
		self.new_password = StringVar()
		self.re_enter_password = StringVar()

		self.current_password_label = Label(master,  text="Enter current password:")
		self.new_password_label = Label(master, text="Enter new password:")
		self.re_enter_password_label = Label(master, text="Re-enter new password:")

		self.current_password_entry = Entry(master, show="*", textvariable=self.current_password)
		self.new_password_entry = Entry(master, show="*", textvariable=self.new_password)
		self.re_enter_password_entry = Entry(master, show="*", textvariable=self.re_enter_password)
		


		self.save_button = Button(master, text="Save", width=13, command=lambda:self.save())

		self.current_password_label.grid(row=0, column=0, padx=(10,10), pady=(10,10))
		self.new_password_label.grid(row=1, column=0, padx=(10,10), pady=(0,10))
		self.re_enter_password_label.grid(row=2, column=0, padx=(10,10), pady=(0,10))

		self.current_password_entry.grid(row=0, column=1, padx=(10,10), pady=(10,10))
		self.new_password_entry.grid(row=1, column=1, padx=(10,10), pady=(0,10))
		self.re_enter_password_entry.grid(row=2, column=1, padx=(10,10), pady=(0,10))

		self.save_button.place(x=170, y=105)

		self.w = 300
		self.h = 140
		centre(self.w, self.h, master)



	def save(self):
		global current_user_id #Declares current_user_id as a global variable 
		current_password_entry = self.current_password_entry.get()
		new_password_entry = self.new_password_entry.get()
		re_enter_password_entry = self.re_enter_password_entry.get()

		current_password_entry_digest = hashlib.sha1(current_password_entry.encode('utf-8')) #Hashes the password using the SHA1 hashing algorithm
		current_password_entry_digest = current_password_entry_digest.hexdigest() #Extracts actual digest in hexadecimal form
		

		current_database_password = self.db.execute("SELECT User_Password FROM User WHERE User_Id=?", (current_user_id,))
		current_database_password = current_database_password.fetchall()[0][0]
		if new_password_entry == "" or re_enter_password_entry == "":
			messagebox.showerror("","Please enter a new password", parent=self.master)
		else:
			if current_database_password == current_password_entry_digest:
				if new_password_entry == re_enter_password_entry:
					new_password_digest = hashlib.sha1(new_password_entry.encode('utf-8')) #Hashes the password using the SHA1 hashing algorithm
					new_password_digest = new_password_digest.hexdigest() #Extracts actual digest in hexadecimal form
					#Updates profiles record in the database
					self.db.execute("UPDATE User SET User_Password = ? WHERE User_Id=?", (new_password_digest, current_user_id,)) 
					self.connection.commit()
					messagebox.showinfo("","New password updated.", parent=self.master)
					self.master.destroy()
				else:
					messagebox.showerror("","The new passwords do not match.", parent=self.master)
			else:
				messagebox.showerror("","The current password you entered is not correct.", parent=self.master)

class Settings():	
	def __init__(self, master):
		self.connection = sqlite3.connect('database.db') #Establishes a connection to the database
		self.db = self.connection.cursor()
		self.master = master
		master.title("Settings")
		self.phone_number = StringVar()
		self.email = StringVar()
		self.logging_in_out = IntVar()
		self.sesame_lock = IntVar()
		self.sesame_email = StringVar()
		self.sesame_password = StringVar()

		self.communication_frame = LabelFrame(master, text="Communication preferences", )
		self.communication_frame.grid(row=0, column=0, pady=(10,10), padx=(10,10), sticky=N)
		self.system_frame = LabelFrame(master, text="System preferences")
		self.system_frame.grid(row=1, column=0, sticky=N)
		self.sesame_frame = LabelFrame(master, text="Sesame smart door lock settings")
		self.sesame_frame.grid(row=0, column=1, pady=(10,0), rowspan=2, sticky=N)

		self.phone_number_label = Label(self.communication_frame, text="Phone number:")
		self.email_label = Label(self.communication_frame, text="Email:")
		self.phone_number_entry = Entry(self.communication_frame, textvariable=self.phone_number)
		self.email_entry = Entry(self.communication_frame, textvariable=self.email) 
		self.phone_number_label.grid(row=0, column=0, pady=(10,10), padx=(10,10))
		self.email_label.grid(row=1, column=0, pady=(0,10,), padx=(10,10), sticky=E)
		self.phone_number_entry.grid(row=0, column=1, pady=(10,10), padx=(0,10))
		self.email_entry.grid(row=1, column=1, pady=(0,10), padx=(0,10))
		self.logging_label = Label(self.system_frame, text="Enable logging in/out")
		self.logging_checkbutton = Checkbutton(self.system_frame, variable=self.logging_in_out)
		self.logging_label.grid(row=0, column=0, pady=(10,10), padx=(30,20))
		self.logging_checkbutton.grid(row=0, column=1, pady=(10,10), padx=(0,40))
		self.sesame_label = Label(self.sesame_frame, text="Enable smart door lock")
		self.sesame_email_label = Label(self.sesame_frame, text="Email")
		self.sesame_password_label = Label(self.sesame_frame, text="Password")
		self.sesame_checkbutton = Checkbutton(self.sesame_frame, variable=self.sesame_lock)
		self.sesame_email_entry = Entry(self.sesame_frame, textvariable=self.sesame_email)
		self.sesame_password_entry = Entry(self.sesame_frame, textvariable=self.sesame_password, show="*")
		self.sesame_label.grid(row=0, column=0, pady=(10,10), padx=(10,10), sticky=E)
		self.sesame_email_label.grid(row=1, column=0, pady=(0,10), padx=(10,10), sticky=E)
		self.sesame_password_label.grid(row=2, column=0, pady=(0,10), padx=(10,10), sticky=E)
		self.sesame_checkbutton.grid(row=0, column=1, pady=(10,10), padx=(0,10))
		self.sesame_email_entry.grid(row=1, column=1, pady=(0,10), padx=(0,10))
		self.sesame_password_entry.grid(row=2, column=1, pady=(0,10), padx=(0,10))

		self.save_button = Button(master, text="Save", width=13, command=lambda:self.save())
		self.save_button.place(x=440, y=145)

		self.w = 560
		self.h = 180
		centre(self.w, self.h, master)
		self.populate_form()

	def populate_form(self):
		self.setting_array = ["Phone_Number", "Email", "Logging_In_Out", "Smart_Lock", "Sesame_Email", "Sesame_Password"]
		setting_values = []
		for setting in self.setting_array:
			query = self.db.execute("SELECT Setting_Value FROM Settings WHERE Setting = ?", (setting,))
			query = query.fetchall()
			setting_values.append(query[0][0])
		self.phone_number_entry.insert(0, setting_values[0])
		self.email_entry.insert(0, setting_values[1])
		self.logging_in_out.set(int(setting_values[2]))
		self.sesame_lock.set(int(setting_values[3]))
		self.sesame_email_entry.insert(0, setting_values[4])
		self.sesame_password_entry.insert(0, setting_values[5])

	def save(self):
		phone_number = self.phone_number_entry.get()
		email = self.email_entry.get()
		logging_in_out = self.logging_in_out.get()
		smart_lock = self.sesame_lock.get()
		sesame_email = self.sesame_email_entry.get()
		sesame_password = self.sesame_password.get()
		phone_number_valid = True 
		setting_values = [phone_number, email, logging_in_out, smart_lock, sesame_email, sesame_password]
		for digit in phone_number: #Checks if phone number only contains digits
			try:
				int(digit)
			except:
				phone_number_valid = False
				break
		if len(phone_number)!=11: #Checks if phone number contains 11 digits 
			phone_number_valid = False
		email_valid = False
		for char in email: #Checks whether the email contains an @ symbol
			if char == "@":
				email_valid = True
		sesame_email_valid = False
		for char in sesame_email: #Checks whether the email for the smart lock contains an @ symbol
			if char == "@":
				sesame_email_valid = True
		if phone_number_valid == False:
			messagebox.showerror("","Please enter a valid phone number", parent=self.master)
		elif email_valid == False:
			messagebox.showerror("","Please enter a valid email", parent=self.master)
		elif sesame_email_valid == False:
			messagebox.showerror("","Please enter a valid sesame smart lock email", parent=self.master)
		else:
			for setting in self.setting_array:
				#Updates profiles record in the database
				self.db.execute("UPDATE Settings SET Setting_Value = ? WHERE Setting = ?", (setting_values[self.setting_array.index(setting)], setting)) 
				self.connection.commit()
			messagebox.showinfo("","Settings successfully saved", parent=self.master)

		

def centre(w, h, window):
	ws = window.winfo_screenwidth() #Gets width of the screen
	hs = window.winfo_screenheight() #Gets height of the screen
	y = (hs/2) - (h/2) #Calculates starting y coordinate of the window
	x = (ws/2) - (w/2) #Calculates starting x coordinate of the window
	window.geometry('%dx%d+%d+%d' % (w, h, x, y)) #Makes the size of the window so it is WxH in size and starts at (x,y)
	window.resizable(0,0) #Prevents window size from being changed







# if __name__ == "__main__":	
# 	root = Tk()
# 	profile_form = Profile_Form(root, "edit")
# 	root.mainloop()

# if __name__ == "__main__":
# 	root = Tk()
# 	report_form = Report_Form(root)
# 	root.mainloop()

# if __name__ == "__main__":
# 	review_log_form_root = Tk()
# 	review_log_form = Review_Log_Form(review_log_form_root, 17)
# 	review_log_form_root.mainloop()

# if __name__ == "__main__":
# 	user_form_root = Tk()
# 	user_form = User_Form(user_form_root, "edit")
# 	user_form_root.mainloop()

# current_user_id = 1
# if __name__ == "__main__":
# 	change_password_root = Tk()
# 	change_password_form = Change_Password(change_password_root)
# 	change_password_root.mainloop()


# if __name__ == "__main__":
# 	settings_root = Tk()
# 	settings_form = Settings(settings_root)
# 	settings_root.mainloop()


# if __name__ == "__main__":
# 	login_root = Tk()
# 	login_form = Login(login_root)
# 	login_root.mainloop()

verify = True
current_access_level = 3
if __name__ == "__main__":
	if verify == True:
		dashboard_root = Tk()
		dashboard = Dashboard(dashboard_root)
		dashboard_root.attributes('-topmost', 'false')
		dashboard_root.mainloop()





