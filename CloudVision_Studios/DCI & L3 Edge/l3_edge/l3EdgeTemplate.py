<%

import json
import re
my_device = ctx.getDevice()
workspace_id = ctx.studio.workspaceId
switch = {} 

# * l3_edge.p2p_links is pointToPointLinks,
# * l3_edge.p2p_links_profiles is pointToPointLinksProfiles,

### Main ###
l3_edge_data = {
    "p2p_interfaces": {},
    "bgp_neighbors": {},
    "ospf_interfaces": [],
    "isis_interfaces": []
}
config = {}
def convert(text):
   return int(text) if text.isdigit() else text.lower()
def alphanum_key(key):
   return [convert(c) for c in re.split('([0-9]+)', str(key))]
def natural_sort(iterable):
   if iterable is None:
      return list()
   return sorted(iterable, key=alphanum_key)

### Logic ###
for p2p_link in pointToPointLinks:
   if p2p_link["linkProfile"] != None and pointToPointLinksProfiles != None:
      p2p_profile = {}
      for profile in pointToPointLinksProfiles:
         if profile['profileName'] == p2p_link['linkProfile']:
            p2p_profile = profile
            break
   else:
      p2p_profile = {}

   #   #   #  Logic Defaults  #    #   #   
   nodes = p2p_link["linkNodes"]
   p2p_interface = {}
   p2p_interface["peer_type"] = str("other")
   p2p_interface["speed"] = p2p_profile.get("profileSpeed") #good
   p2p_interface["mtu"] = p2p_profile.get("profileMtu") # = p2p_uplinks_mtu # good
   p2p_interface["qos_profile"] = p2p_profile.get("profileQosProfile") # good
   p2p_interface["macsec_profile"] = p2p_profile.get("profileMacsecProfile")
   p2p_interface["ptp_enable"] = p2p_profile.get("profilePtpEnable")
   asn = p2p_profile.get("profileAsns")
   p2p_bgp_neighbor = {}
   p2p_bgp_neighbor["bfd"] = p2p_profile.get("profileBfd")
   #   #   #   #   #   #   #   #   #   #   #   

   if my_device.hostName in p2p_link["linkNodes"]:  
      node_index = nodes.index(my_device.hostName)
      peer_index = 1 - node_index
      ip_list = p2p_link["linkIpAddresses"] 
      interfaces = p2p_link["linkInterfaces"] 
      node_interface = interfaces[node_index] 
      p2p_interface["peer"] = nodes[peer_index]   
      p2p_interface["peer_interface"] = interfaces[peer_index]     
      p2p_interface["speed"] = p2p_link["linkSpeed"]
      if ip_list != None:   
         p2p_interface["ip_address"] = ip_list[node_index]
         p2p_interface["peer_ip"] = ip_list[peer_index].split("/")[0]
      elif subnet != None:
         mask = subnet 
         p2p_interface["ip_address"] = subnet                      
         p2p_interface["peer_ip"] = subnet      
      p2p_interface["mtu"] = p2p_link["linkMtu"] 
      p2p_interface["qos_profile"] = p2p_link["linkQosProfile"]        
      p2p_interface["macsec_profile"] = p2p_link["linkMacsecProfile"]  
      p2p_interface["ptp_enable"] = p2p_link["linkPtpEnable"]          
      p2p_interface["type"] = "routed"
      p2p_interface["shutdown"] = "false"
      p2p_interface["description"] = "P2P_LINK_TO_" + p2p_interface["peer"] + "_" + p2p_interface["peer_interface"] 
      if p2p_link["linkRoutingDetails"]["linkIncludeInRoutingProtocol"] == True: 
         l3_edge_data["underlay_routing_protocol"] = p2p_link["linkRoutingDetails"]["linkUnderlayRoutingProtocol"]
      l3_edge_data["p2p_interfaces"] = {node_interface: p2p_interface}         
      if p2p_link["linkRoutingDetails"]["linkIncludeInRoutingProtocol"] == True: 
         if p2p_link["linkRoutingDetails"]["linkUnderlayRoutingProtocol"] == "bgp": 
            asn = p2p_link["linkAsns"]
            p2p_bgp_neighbor = {}
            p2p_bgp_neighbor["remote_as"] = asn[peer_index] 
            p2p_bgp_neighbor["description"] = p2p_interface["peer"]
            p2p_bgp_neighbor["bfd"] = p2p_link["linkBfd"]    
            l3_edge_data["bgp_neighbors"] = {p2p_interface["peer_ip"]: p2p_bgp_neighbor}        

### ethernet-interfaces ###
ethernet_interfaces = {}
if len(l3_edge_data["p2p_interfaces"]) > 0:
   for p2p_interface_key in l3_edge_data["p2p_interfaces"]:
      p2p_interface = l3_edge_data["p2p_interfaces"][p2p_interface_key]
      ethernet_interfaces[p2p_interface_key] = {}
      ethernet_interfaces[p2p_interface_key]["peer"] = p2p_interface["peer"]
      ethernet_interfaces[p2p_interface_key]["peer_interface"] = p2p_interface["peer_interface"]
      ethernet_interfaces[p2p_interface_key]["peer_type"] = p2p_interface["peer_type"]
      ethernet_interfaces[p2p_interface_key]["description"] = p2p_interface["description"]
      ethernet_interfaces[p2p_interface_key]["type"] = p2p_interface["type"]
      ethernet_interfaces[p2p_interface_key]["shutdown"] = p2p_interface["shutdown"]
      ethernet_interfaces[p2p_interface_key]["mtu"] = p2p_interface["mtu"]
      if p2p_interface["ip_address"] != None:
         ethernet_interfaces[p2p_interface_key]["ip_address"] = p2p_interface["ip_address"]
      if p2p_interface["speed"] != None:
         ethernet_interfaces[p2p_interface_key]["speed"] = p2p_interface["speed"]
      if p2p_interface["qos_profile"] != None:
         ethernet_interfaces[p2p_interface_key]["service_profile"] = p2p_interface["qos_profile"]
      if p2p_interface["macsec_profile"] != None:
         ethernet_interfaces[p2p_interface_key]["mac_security"] = {}
         ethernet_interfaces[p2p_interface_key]["mac_security"]["profile"] = p2p_interface["macsec_profile"]
      if p2p_interface["ptp_enable"] == True:
         ethernet_interfaces[p2p_interface_key]["ptp"] = {}
         ethernet_interfaces[p2p_interface_key]["ptp"]["enable"] = True

### router-bgp-neighbors ###
router_bgp = {}
if len(l3_edge_data["bgp_neighbors"]) > 0:
   router_bgp["neighbors"] = {}
   for bgp_neighbor_key in l3_edge_data["bgp_neighbors"]:
      bgp_neighbor = l3_edge_data["bgp_neighbors"][bgp_neighbor_key]
      router_bgp["neighbors"][bgp_neighbor_key]={}
      router_bgp["as"] = asn 
      router_bgp["neighbors"][bgp_neighbor_key]["remote_as"] = bgp_neighbor["remote_as"]
      router_bgp["neighbors"][bgp_neighbor_key]["description"] = bgp_neighbor["description"]
      if bgp_neighbor["bfd"] == True:
         router_bgp["neighbors"][bgp_neighbor_key]["bfd"] = True

### Structured Config ###
config["ethernet_interfaces"] = ethernet_interfaces
config["router_bgp"] = router_bgp

%>

## eos - Ethernet Interfaces
%if config.get("ethernet_interfaces") is not None:
%for ethernet_interface in natural_sort(config["ethernet_interfaces"].keys()):
interface ${ethernet_interface }
%     if config["ethernet_interfaces"][ethernet_interface]["description"] is not None:
description ${config["ethernet_interfaces"][ethernet_interface]["description"]}
%     endif
%     if config["ethernet_interfaces"][ethernet_interface].get("channel_group") is not None:
channel-group ${ config["ethernet_interfaces"][ethernet_interface]["channel_group"]["id"] } mode ${ config["ethernet_interfaces"][ethernet_interface]["channel_group"]["mode"] }
%     else:
%         if config["ethernet_interfaces"][ethernet_interface].get("mtu") is not None:
mtu ${ config["ethernet_interfaces"][ethernet_interface]["mtu"] }
%         endif
%         if config["ethernet_interfaces"][ethernet_interface].get("ip_address") is not None:
ip address ${ config["ethernet_interfaces"][ethernet_interface].get("ip_address") }
%         endif
%     endif
!
%endfor
%endif


## router-bgp
% if config.get("router_bgp") is not None:
% if config["router_bgp"].get("as") is not None:
router bgp ${asn[node_index]}
%     if config["router_bgp"].get("router_id") is not None:
   router-id ${ config["router_bgp"]["router_id"] }
%     endif
%     if config["router_bgp"].get("bgp_defaults") is not None:
%       for bgp_default in config["router_bgp"]["bgp_defaults"]:
   ${ bgp_default }
%       endfor
%     endif
%     if config["router_bgp"].get("peer_groups") is not None:
%     for peer_group in config["router_bgp"]["peer_groups"].keys():
%         if config["router_bgp"]["peer_groups"][peer_group].get("description") is not None:
   neighbor ${ peer_group } description ${ config["router_bgp"]["peer_groups"][peer_group]["description"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("shutdown") == True:
   neighbor ${ peer_group } shutdown
%         endif
   neighbor ${ peer_group } peer group
%         if config["router_bgp"]["peer_groups"][peer_group].get("remote_as") is not None:
   neighbor ${ peer_group } remote-as ${ config["router_bgp"]["peer_groups"][peer_group]["remote_as"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("local_as") is not None:
   neighbor ${ peer_group } local-as ${ config["router_bgp"]["peer_groups"][peer_group]["local_as"] } no-prepend replace-as
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("next_hop_self") == True:
   neighbor ${ peer_group } next-hop-self
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("next_hop_unchanged") == True:
   neighbor ${ peer_group } next-hop-unchanged
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("update_source") is not None:
   neighbor ${ peer_group } update-source ${ config["router_bgp"]["peer_groups"][peer_group]["update_source"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("route_reflector_client") == True:
   neighbor ${ peer_group } route-reflector-client
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("bfd") == True:
   neighbor ${ peer_group } bfd
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("ebgp_multihop") is not None:
   neighbor ${ peer_group } ebgp-multihop ${ config["router_bgp"]["peer_groups"][peer_group]["ebgp_multihop"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("password") is not None:
   neighbor ${ peer_group } password 7 ${ config["router_bgp"]["peer_groups"][peer_group]["password"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("send_community") is not None and config["router_bgp"]["peer_groups"][peer_group]["send_community"] == "all":
   neighbor ${ peer_group } send-community
%         elif config["router_bgp"]["peer_groups"][peer_group].get("send_community") is not None:
   neighbor ${ peer_group } send-community ${ config["router_bgp"]["peer_groups"][peer_group]["send_community"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("maximum_routes") is not None and config["router_bgp"]["peer_groups"][peer_group].get("maximum_routes_warning_limit") is not None:
   neighbor ${ peer_group } maximum-routes ${ config["router_bgp"]["peer_groups"][peer_group]["maximum_routes"] } warning-limit ${ config["router_bgp"]["peer_groups"][peer_group]["maximum_routes_warning_limit"] }
%         elif config["router_bgp"]["peer_groups"][peer_group].get("maximum_routes") is not None:
   neighbor ${ peer_group } maximum-routes ${ config["router_bgp"]["peer_groups"][peer_group]["maximum_routes"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("route_map_in") is not None:
   neighbor ${ peer_group } route-map ${ config["router_bgp"]["peer_groups"][peer_group]["route_map_in"] } in
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("route_map_out") is not None:
   neighbor ${ peer_group } route-map ${ config["router_bgp"]["peer_groups"][peer_group]["route_map_out"] } out
%         endif
%       endfor
%     endif
%     if config["router_bgp"].get("neighbors") is not None:
%       for neighbor in config["router_bgp"]["neighbors"].keys():
%         if config["router_bgp"]["neighbors"][neighbor].get("peer_group") is not None:
   neighbor ${ neighbor } peer group ${ config["router_bgp"]["neighbors"][neighbor]["peer_group"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("remote_as") is not None:
   neighbor ${ neighbor } remote-as ${ config["router_bgp"]["neighbors"][neighbor]["remote_as"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("next_hop_self") == True:
   neighbor ${ neighbor } next-hop-self
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("shutdown") == True:
   neighbor ${ neighbor } shutdown
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("local_as") is not None:
   neighbor ${ neighbor } local-as ${ config["router_bgp"]["neighbors"][neighbor]["local_as"] } no-prepend replace-as
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("description") is not None:
   neighbor ${ neighbor } description ${ config["router_bgp"]["neighbors"][neighbor]["description"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("update_source") is not None:
   neighbor ${ neighbor } update-source ${ config["router_bgp"]["neighbors"][neighbor]["update_source"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("bfd") == True:
   neighbor ${ neighbor } bfd
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("password") is not None:
   neighbor ${ neighbor } password 7 ${ config["router_bgp"]["neighbors"][neighbor]["password"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("weight") is not None:
   neighbor ${ neighbor } weight ${ config["router_bgp"]["neighbors"][neighbor]["weight"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("timers") is not None:
   neighbor ${ neighbor } timers ${ config["router_bgp"]["neighbors"][neighbor]["timers"] }
%         endif
%       endfor
%     endif
% endif
% endif



######################################################################################################
######################################################################################################


<%
import json
import re
my_device = ctx.getDevice()
workspace_id = ctx.studio.workspaceId
switch = {} 
config = {}
l3_edge_data = {
    "p2p_interfaces": {},
    "bgp_neighbors": {},
    "ospf_interfaces": [],
    "isis_interfaces": []
}

# * l3_edge.p2p_links is pointToPointLinks,
# * l3_edge.p2p_links_profiles is pointToPointLinksProfiles,

def convert(text):
   return int(text) if text.isdigit() else text.lower()
def alphanum_key(key):
   return [convert(c) for c in re.split('([0-9]+)', str(key))]
def natural_sort(iterable):
   if iterable is None:
      return list()
   return sorted(iterable, key=alphanum_key)

### Logic ###
for p2p_link in pointToPointLinks:
   if p2p_link["linkProfile"] != None and pointToPointLinksProfiles != None:
      p2p_profile = {}
      ctx.info(f"{pointToPointLinksProfiles}")
      for profile in pointToPointLinksProfiles:
         if profile['profileName'] == p2p_link['linkProfile']:
            p2p_profile = profile
            break
   else:
      p2p_profile = {}

   #   #   #  Logic Defaults  #    #   #   
   nodes = p2p_link["linkNodes"]
   p2p_interface = {}
   p2p_interface["peer_type"] = str("other")
   p2p_interface["speed"] = p2p_profile.get("profileSpeed") #good
   p2p_interface["mtu"] = p2p_profile.get("profileMtu") # = p2p_uplinks_mtu # good
   p2p_interface["qos_profile"] = p2p_profile.get("profileQosProfile") # good
   p2p_interface["macsec_profile"] = p2p_profile.get("profileMacsecProfile")
   p2p_interface["ptp_enable"] = p2p_profile.get("profilePtpEnable")
   asn = p2p_profile.get("profileAsns")
   p2p_bgp_neighbor = {}
   p2p_bgp_neighbor["bfd"] = p2p_profile.get("profileBfd")
   #   #   #   #   #   #   #   #   #   #   #   

   if my_device.hostName in p2p_link["linkNodes"]:  
      node_index = nodes.index(my_device.hostName)
      peer_index = 1 - node_index
      ip_list = p2p_link["linkIpAddresses"] 
      interfaces = p2p_link["linkInterfaces"] 
      node_interface = interfaces[node_index] 
      ctx.info(f"nodes[peer_index]:\n{nodes[peer_index]}")
      p2p_interface["peer"] = nodes[peer_index]  
      p2p_interface["peer_interface"] = interfaces[peer_index]     
      p2p_interface["speed"] = p2p_link["linkSpeed"]
      if ip_list != None:   
         p2p_interface["ip_address"] = ip_list[node_index]
         p2p_interface["peer_ip"] = ip_list[peer_index].split("/")[0]
      elif subnet != None:
         mask = subnet 
         p2p_interface["ip_address"] = subnet                      
         p2p_interface["peer_ip"] = subnet      
      p2p_interface["mtu"] = p2p_link["linkMtu"] 
      p2p_interface["qos_profile"] = p2p_link["linkQosProfile"]        
      p2p_interface["macsec_profile"] = p2p_link["linkMacsecProfile"]  
      p2p_interface["ptp_enable"] = p2p_link["linkPtpEnable"]          
      p2p_interface["type"] = "routed"
      p2p_interface["shutdown"] = "false"
      p2p_interface["description"] = "P2P_LINK_TO_" + p2p_interface["peer"] + "_" + p2p_interface["peer_interface"] 
      if p2p_link["linkRoutingDetails"]["linkIncludeInRoutingProtocol"] == True: 
         l3_edge_data["underlay_routing_protocol"] = p2p_link["linkRoutingDetails"]["linkUnderlayRoutingProtocol"]
      l3_edge_data["p2p_interfaces"] = {node_interface: p2p_interface}         
      if p2p_link["linkRoutingDetails"]["linkIncludeInRoutingProtocol"] == True: 
         if p2p_link["linkRoutingDetails"]["linkUnderlayRoutingProtocol"] == "bgp": 
            asn = p2p_link["linkAsns"]
            p2p_bgp_neighbor = {}
            # p2p_bgp_neighbor["remote_as"] = asn[peer_index] 
            p2p_bgp_neighbor["description"] = p2p_interface["peer"]
            p2p_bgp_neighbor["bfd"] = p2p_link["linkBfd"]    
            # l3_edge_data["bgp_neighbors"] = {p2p_interface["peer_ip"]: p2p_bgp_neighbor}        

### ethernet-interfaces ###
ethernet_interfaces = {}
if len(l3_edge_data["p2p_interfaces"]) > 0:
   for p2p_interface_key in l3_edge_data["p2p_interfaces"]:
      p2p_interface = l3_edge_data["p2p_interfaces"][p2p_interface_key]
      ethernet_interfaces[p2p_interface_key] = {}
      ethernet_interfaces[p2p_interface_key]["peer"] = p2p_interface["peer"]
      ethernet_interfaces[p2p_interface_key]["peer_interface"] = p2p_interface["peer_interface"]
      ethernet_interfaces[p2p_interface_key]["peer_type"] = p2p_interface["peer_type"]
      ethernet_interfaces[p2p_interface_key]["description"] = p2p_interface["description"]
      ethernet_interfaces[p2p_interface_key]["type"] = p2p_interface["type"]
      ethernet_interfaces[p2p_interface_key]["shutdown"] = p2p_interface["shutdown"]
      ethernet_interfaces[p2p_interface_key]["mtu"] = p2p_interface["mtu"]
      if p2p_interface["ip_address"] != None:
         ethernet_interfaces[p2p_interface_key]["ip_address"] = p2p_interface["ip_address"]
      if p2p_interface["speed"] != None:
         ethernet_interfaces[p2p_interface_key]["speed"] = p2p_interface["speed"]
      if p2p_interface["qos_profile"] != None:
         ethernet_interfaces[p2p_interface_key]["service_profile"] = p2p_interface["qos_profile"]
      if p2p_interface["macsec_profile"] != None:
         ethernet_interfaces[p2p_interface_key]["mac_security"] = {}
         ethernet_interfaces[p2p_interface_key]["mac_security"]["profile"] = p2p_interface["macsec_profile"]
      if p2p_interface["ptp_enable"] == True:
         ethernet_interfaces[p2p_interface_key]["ptp"] = {}
         ethernet_interfaces[p2p_interface_key]["ptp"]["enable"] = True

### router-bgp-neighbors ###
router_bgp = {}
if len(l3_edge_data["bgp_neighbors"]) > 0:
   router_bgp["neighbors"] = {}
   for bgp_neighbor_key in l3_edge_data["bgp_neighbors"]:
      bgp_neighbor = l3_edge_data["bgp_neighbors"][bgp_neighbor_key]
      router_bgp["neighbors"][bgp_neighbor_key]={}
      router_bgp["as"] = asn 
      router_bgp["neighbors"][bgp_neighbor_key]["remote_as"] = bgp_neighbor["remote_as"]
      router_bgp["neighbors"][bgp_neighbor_key]["description"] = bgp_neighbor["description"]
      if bgp_neighbor["bfd"] == True:
         router_bgp["neighbors"][bgp_neighbor_key]["bfd"] = True

### Structured Config ###
config["ethernet_interfaces"] = ethernet_interfaces
config["router_bgp"] = router_bgp

%>

## eos - Ethernet Interfaces
%if config.get("ethernet_interfaces") is not None:
%for ethernet_interface in natural_sort(config["ethernet_interfaces"].keys()):
interface ${ethernet_interface }
%     if config["ethernet_interfaces"][ethernet_interface]["description"] is not None:
description ${config["ethernet_interfaces"][ethernet_interface]["description"]}
%     endif
%     if config["ethernet_interfaces"][ethernet_interface].get("channel_group") is not None:
channel-group ${ config["ethernet_interfaces"][ethernet_interface]["channel_group"]["id"] } mode ${ config["ethernet_interfaces"][ethernet_interface]["channel_group"]["mode"] }
%     else:
%         if config["ethernet_interfaces"][ethernet_interface].get("mtu") is not None:
mtu ${ config["ethernet_interfaces"][ethernet_interface]["mtu"] }
%         endif
%         if config["ethernet_interfaces"][ethernet_interface].get("ip_address") is not None:
ip address ${ config["ethernet_interfaces"][ethernet_interface].get("ip_address") }
%         endif
%     endif
!
%endfor
%endif


## router-bgp
% if config.get("router_bgp") is not None:
% if config["router_bgp"].get("as") is not None:
router bgp ${asn[node_index]}
%     if config["router_bgp"].get("router_id") is not None:
   router-id ${ config["router_bgp"]["router_id"] }
%     endif
%     if config["router_bgp"].get("bgp_defaults") is not None:
%       for bgp_default in config["router_bgp"]["bgp_defaults"]:
   ${ bgp_default }
%       endfor
%     endif
%     if config["router_bgp"].get("peer_groups") is not None:
%     for peer_group in config["router_bgp"]["peer_groups"].keys():
%         if config["router_bgp"]["peer_groups"][peer_group].get("description") is not None:
   neighbor ${ peer_group } description ${ config["router_bgp"]["peer_groups"][peer_group]["description"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("shutdown") == True:
   neighbor ${ peer_group } shutdown
%         endif
   neighbor ${ peer_group } peer group
%         if config["router_bgp"]["peer_groups"][peer_group].get("remote_as") is not None:
   neighbor ${ peer_group } remote-as ${ config["router_bgp"]["peer_groups"][peer_group]["remote_as"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("local_as") is not None:
   neighbor ${ peer_group } local-as ${ config["router_bgp"]["peer_groups"][peer_group]["local_as"] } no-prepend replace-as
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("next_hop_self") == True:
   neighbor ${ peer_group } next-hop-self
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("next_hop_unchanged") == True:
   neighbor ${ peer_group } next-hop-unchanged
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("update_source") is not None:
   neighbor ${ peer_group } update-source ${ config["router_bgp"]["peer_groups"][peer_group]["update_source"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("route_reflector_client") == True:
   neighbor ${ peer_group } route-reflector-client
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("bfd") == True:
   neighbor ${ peer_group } bfd
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("ebgp_multihop") is not None:
   neighbor ${ peer_group } ebgp-multihop ${ config["router_bgp"]["peer_groups"][peer_group]["ebgp_multihop"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("password") is not None:
   neighbor ${ peer_group } password 7 ${ config["router_bgp"]["peer_groups"][peer_group]["password"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("send_community") is not None and config["router_bgp"]["peer_groups"][peer_group]["send_community"] == "all":
   neighbor ${ peer_group } send-community
%         elif config["router_bgp"]["peer_groups"][peer_group].get("send_community") is not None:
   neighbor ${ peer_group } send-community ${ config["router_bgp"]["peer_groups"][peer_group]["send_community"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("maximum_routes") is not None and config["router_bgp"]["peer_groups"][peer_group].get("maximum_routes_warning_limit") is not None:
   neighbor ${ peer_group } maximum-routes ${ config["router_bgp"]["peer_groups"][peer_group]["maximum_routes"] } warning-limit ${ config["router_bgp"]["peer_groups"][peer_group]["maximum_routes_warning_limit"] }
%         elif config["router_bgp"]["peer_groups"][peer_group].get("maximum_routes") is not None:
   neighbor ${ peer_group } maximum-routes ${ config["router_bgp"]["peer_groups"][peer_group]["maximum_routes"] }
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("route_map_in") is not None:
   neighbor ${ peer_group } route-map ${ config["router_bgp"]["peer_groups"][peer_group]["route_map_in"] } in
%         endif
%         if config["router_bgp"]["peer_groups"][peer_group].get("route_map_out") is not None:
   neighbor ${ peer_group } route-map ${ config["router_bgp"]["peer_groups"][peer_group]["route_map_out"] } out
%         endif
%       endfor
%     endif
%     if config["router_bgp"].get("neighbors") is not None:
%       for neighbor in config["router_bgp"]["neighbors"].keys():
%         if config["router_bgp"]["neighbors"][neighbor].get("peer_group") is not None:
   neighbor ${ neighbor } peer group ${ config["router_bgp"]["neighbors"][neighbor]["peer_group"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("remote_as") is not None:
   neighbor ${ neighbor } remote-as ${ config["router_bgp"]["neighbors"][neighbor]["remote_as"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("next_hop_self") == True:
   neighbor ${ neighbor } next-hop-self
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("shutdown") == True:
   neighbor ${ neighbor } shutdown
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("local_as") is not None:
   neighbor ${ neighbor } local-as ${ config["router_bgp"]["neighbors"][neighbor]["local_as"] } no-prepend replace-as
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("description") is not None:
   neighbor ${ neighbor } description ${ config["router_bgp"]["neighbors"][neighbor]["description"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("update_source") is not None:
   neighbor ${ neighbor } update-source ${ config["router_bgp"]["neighbors"][neighbor]["update_source"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("bfd") == True:
   neighbor ${ neighbor } bfd
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("password") is not None:
   neighbor ${ neighbor } password 7 ${ config["router_bgp"]["neighbors"][neighbor]["password"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("weight") is not None:
   neighbor ${ neighbor } weight ${ config["router_bgp"]["neighbors"][neighbor]["weight"] }
%         endif
%         if config["router_bgp"]["neighbors"][neighbor].get("timers") is not None:
   neighbor ${ neighbor } timers ${ config["router_bgp"]["neighbors"][neighbor]["timers"] }
%         endif
%       endfor
%     endif
% endif
% endif


