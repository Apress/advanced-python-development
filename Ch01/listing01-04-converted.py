#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sys
sys.version_info


# In[4]:


import socket
hostname = socket.gethostname()

addresses = socket.getaddrinfo(hostname, None)

for address in addresses:
    print(address[0].name, address[4][0])


# In[5]:


import psutil


# In[6]:


psutil.cpu_percent()


# In[7]:


psutil.virtual_memory().available


# In[8]:


psutil.sensors_battery().power_plugged


# In[ ]:




