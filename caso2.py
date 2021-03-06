#!/usr/bin_/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

class myNetwork(): 

    #constructor 
    def __init__(self, n):
        self.n = n #numero de sucursales  
        self.net = Mininet( topo=None,
                    build=False,
                    ipBase='10.0.0.0/8')

        self.sucursales = []
        info( '*** Adding controller\n' )
        info( '*** Add switches\n')
        info( '*** Add hosts\n')

        
        for i in range(1,self.n+1):
            self.nombre_variable_s_lan = 's{}_lan'.format(i)
            self.nombre_variable_s_wan = 's{}_wan'.format(i)
            self.nombre_variable_r = 'r{}'.format(i)
            self.nombre_variable_h = 'h{}'.format(i)

            globals()[self.nombre_variable_s_lan] = self.net.addSwitch(self.nombre_variable_s_lan, cls=OVSKernelSwitch, failMode='standalone')
            globals()[self.nombre_variable_s_wan] = self.net.addSwitch(self.nombre_variable_s_wan, cls=OVSKernelSwitch, failMode='standalone')
            globals()[self.nombre_variable_r] = self.net.addHost(self.nombre_variable_r, cls=Node, ip='')
            self.sucursales.append(i)
            globals()[self.nombre_variable_r].cmd('sysctl -w net.ipv4.ip_forward=1')
            globals()[self.nombre_variable_h] = self.net.addHost(self.nombre_variable_h, cls=Node, ip='10.0.{}.254/24'.format(i), defaultRoute='via 10.0.{}.1'.format(i))
        # siempre va a estar el central -- crear dsps de los switchs pq si no salta error
        self.r_central = self.net.addHost('r_central', cls=Node, ip='')
        self.r_central.cmd('sysctl -w net.ipv4.ip_forward=1')
        self.primera_ip_4to = 1
        self.ultima_ip_4to = 6


    #CREACION DE LINKS 
    def add_links(self):
        info( '*** Add links\n')
        for i in range(1,self.n+1):
            self.net.addLink(self.r_central, globals()['s{}_wan'.format(i)], intfName1='r_central-eth{}'.format(i-1), params1={ 'ip' : '192.168.100.{}/29'.format(self.ultima_ip_4to)})
            self.net.addLink(globals()['r{}'.format(i)], globals()['s{}_wan'.format(i)], intfName1='r1-eth{}'.format(i-1), params1={ 'ip' : '192.168.100.{}/29'.format(self.primera_ip_4to)})
            self.net.addLink(globals()['r{}'.format(i)], globals()['s{}_lan'.format(i)], intfName1='r{}-eth1'.format(i), params1={ 'ip' : '10.0.{}.1/24'.format(i) })
            self.net.addLink(globals()['h{}'.format(i)], globals()['s{}_lan'.format(i)])
            self.primera_ip_4to += 8
            self.ultima_ip_4to += 8
    

    def start_network(self):
        info( '*** Starting network\n')
        self.net.build()
        info( '*** Starting controllers\n')
        for controller in self.net.controllers:
            controller.start()


    def start_switches(self):
        info( '*** Starting switches\n')
        for i in range(1,self.n+1):
            self.net.get('s{}_wan'.format(i)).start([])
            self.net.get('s{}_lan'.format(i)).start([])

    #creamos tabla de ruteo!
    def routing_table_conf(self):
        info( '*** Post configure switches and hosts\n')
        base_ip = 1
        for i in range(self.n):
            self.net['r_central'].cmd('ip route add 10.0.{}.0/24 via 192.168.100.{}'.format(i+1, base_ip))

            for j in range(self.n):
                self.net['r{}'.format(i+1)].cmd('ip route add 10.0.{}.0/24 via 192.168.100.{}'.format(j+1, base_ip+5))
                
            base_ip += 8

        CLI(self.net)
        self.net.stop()



if __name__ == '__main__':
    setLogLevel( 'info' )
    my_network2 = myNetwork(3)
    my_network2.add_links()
    my_network2.start_network()
    my_network2.start_switches()
    my_network2.routing_table_conf()