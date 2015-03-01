import sublime, sublime_plugin

import Collab.server as Server
import Collab.client as Client

serverInstance = Server.Server()
clientInstance = Client.Client()


class Collab_listenCommand(sublime_plugin.TextCommand):
	def run(self, edit,port):
		newWindow = sublime.active_window()
		if serverInstance.listen(port,newWindow):
			print("Collab - Listening on Port : "+ str(port))
		else:
			print("Collab - Error attempting to Listen")




class Collab_debugconnectCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.window().run_command('new_window')
		newWindow = sublime.active_window()
		clientInstance.connect('fob.x539.me',28020,"Jeffy",newWindow)

class Collab_localpeersCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		for peer in clientInstance.peers:
			print(peer)
			print(peer.name)




class CollabEvents( sublime_plugin.EventListener ):
	def on_modified( self, view ):
		s = view.sel()
		line = view.full_line(s[0].a-1)
		linectn = view.substr(line)
		if serverInstance.listening:
			serverInstance.testbroadcast(view.id(),line,linectn)


class insertData( sublime_plugin.TextCommand ):
	def run( self, edit, position, data ):
		self.view.insert( edit, position, data )


class replaceData( sublime_plugin.TextCommand ):
	def run( self, edit, positiona, positionb,data ):
		self.view.replace( edit, sublime.Region(positiona,positionb), data )