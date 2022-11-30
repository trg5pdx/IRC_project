# IRC_project

This is a basic IRC client/server that's written using a custom protocol, don't 
use it for any genuine communications, as the server doesn't encrypt any messages,
and probably has other issues with it that would make it non ideal. 

To checkout the project you will need python3 installed on your system in order
to run it. Once you have that, go into a directory that you want to run this in,
and run the following command from your terminal:

`git clone https://github.com/trgpdx/IRC_project`

And to run the server, cd over to the server/ directory and run

`python Server.py`

You can also supply an address and a port to the server, like below

`python Server.py localhost 2000`

And to run the client, cd over to the client/ directory and run

`python Client.py`

You can also supply an address and a port to the client, like below

`python Client.py localhost 2000`
