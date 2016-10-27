try:
	import Queue as Q
except ImportError:
	import queue as Q

from collections import defaultdict
import argparse
import datetime
from datetime import timedelta
try:
	from geopy.distance import great_circle
except ImportError:
	raise ImportError('Please Install geopy python library (pip install geopy)')


parser = argparse.ArgumentParser()
parser.add_argument("--startnode", help="Enter Start Node", type=str)
parser.add_argument("--endnode", help="Enter Destination Node", type=str)
parser.add_argument("--starttime", help="Enter time when you want to start the journey in HH:MM:SS format", type=str)
args = parser.parse_args()

source = args.startnode
destination = args.endnode
depart = args.starttime



graph_file = "j-AdjList_Thursday.txt"
gps_file = "j-Nodes.csv"
gps = {}
with open(gps_file,"r") as f1:
	for line in f1:
		p = line.rstrip("\n").split(",")
		gps[p[0]] = (float(p[1]),float(p[2]))

inter = {}
with open("inter.csv","r") as f2:
	flag = 0
	for line in f2:
		if flag == 0:
			flag += 1
			continue
		p = line.rstrip("\n").split(",")
		inter[(int(p[0]),int(p[1]))] = float(p[2])

intra = {}
with open("intra.csv","r") as f3:
	flag = 0
	for line in f3:
		if flag == 0:
			flag += 1
			continue
		p = line.rstrip("\n").split(",")
		node = "n" + str(p[0])
		partition = int(p[1])
		from_border = float(p[3])
		to_border = float(p[4])
		intra[node] = {"partition":partition,"border_to_node":from_border,"node_to_border":to_border}


def build_graph():
	graph = {}
	with open(graph_file,"r") as f:
		for line in f:
			fromnode = line.split("|")[0]
			graph[fromnode] = []
			p = line.split("|")[1].split(";")
			for item in p:
				graph[fromnode].append( (item.split(":")[0].rstrip("(V)"), item.rstrip("\n").split(":")[1].split(",")) )

	return graph
		

def reconstruct_path(cameFrom, current, time_at_this_node):
	total_path = [(current, time_at_this_node[current].strftime('%H:%M:%S'))]
	while current in cameFrom.keys():
		current = cameFrom[current]
		total_path.append((current, time_at_this_node[current].strftime('%H:%M:%S')))
	return total_path

def heuristic_cost_estimate(neighbor, goal):
	
	# First get the partitions of both nodes
	part1 = intra[neighbor]["partition"]
	part2 = intra[goal]["partition"]
	if part1 != part2:
		cost = intra[neighbor]["node_to_border"] + inter[(part1,part2)] + intra[goal]["border_to_node"]
	else:
		dist = great_circle(gps[neighbor], gps[goal]).miles
		cost = (float(dist)/float(80)) * 60 * 60 * 1000

	return cost

def partition_astar(start, goal, start_time):
	graph = build_graph()
	closedSet = []
	openSet = Q.PriorityQueue()
	
	cameFrom = {}
	time_at_this_node = defaultdict(lambda: None)
	time_at_this_node[start] = datetime.datetime.strptime(start_time,"%H:%M:%S")
	tdelta = datetime.timedelta(milliseconds=1)
	# For each node, the cost of getting from the start node to that node.
	gScore = defaultdict(lambda: float("inf"))
	# The cost of going from start to start is zero.
	gScore[start] = 0 
	# For each node, the total cost of getting from the start node to the goal
	# by passing by that node. That value is partly known, partly heuristic.
	fScore = defaultdict(lambda: float("inf"))
	# For the first node, that value is completely heuristic.
	fScore[start] = heuristic_cost_estimate(start, goal)
	openSet.put((fScore[start], start))

	while not openSet.empty():
		tt = openSet.get()
		print time_at_this_node[tt[1]].strftime('%H:%M:%S') + " chosen: ", str(tt)
		current = tt[1]
		current_fscore = tt[0]
		if current == goal:
			print "Goal Reached"
			return reconstruct_path(cameFrom, current,time_at_this_node)

		# Do not need to do the below step as openSet.get() already removes it
		#openSet.Remove(current)
		closedSet.append((current,current_fscore))
		for item in graph[current]:
			neighbor = item[0]
			neighbor_costs = item[1]
			flag = 0
			if neighbor in [l[0] for l in closedSet]:
				flag = 1
				print "	(CLOSED)", neighbor,
			else:
				print "	",neighbor,
			
			#Time Dependent cost calculation
			curnode_time = time_at_this_node[current]
			if len(neighbor_costs) == 1:
				cost_to_neighbor = int(neighbor_costs[0])
			else:
				timestr = curnode_time.strftime('%H:%M:%S')
				minutes = int(timestr.split(":")[1])
				hours = int(timestr.split(":")[0])
				if minutes>=0 and minutes < 15:
					index = ((hours-6)*4) - 1 + 1
				elif minutes>=15 and minutes < 30:
					index = ((hours-6)*4) - 1 + 2
				elif minutes>=30 and minutes < 45:
					index = ((hours-6)*4) - 1 + 3
				else:
					index = ((hours-6)*4) - 1 + 4
				cost_to_neighbor = int(neighbor_costs[index])


			# The distance from start to a neighbor
			tentative_gScore = gScore[current] + cost_to_neighbor
			if neighbor not in [item[1] for item in openSet.queue]:	# Discover a new node
				fs = tentative_gScore + heuristic_cost_estimate(neighbor, goal)
				print str(fs)
				if flag== 1:
					for kl in closedSet:
						if kl[0] == neighbor:
							x = kl[1]
					if fs < x :
						print "yes",neighbor
						openSet.put((fs, neighbor))
					else:
						continue

				else:
					openSet.put((fs, neighbor))
			elif tentative_gScore >= gScore[neighbor]:
				continue		# This is not a better path.

			# This path is the best until now. Record it!
			cameFrom[neighbor] = current
			gScore[neighbor] = tentative_gScore
			fScore[neighbor] = gScore[neighbor] + heuristic_cost_estimate(neighbor, goal)
			time_at_this_node[neighbor] = (cost_to_neighbor*tdelta) + curnode_time

	return -1

if __name__ == "__main__":
	path = partition_astar(source,destination,depart)
	path1 = path[:]
	path = reversed(path)
	path1 = reversed(path1)
	
	
	
	with open("partition_path.txt","w") as pp:
		content = ""
		for item in path:
			content += str(item) + "\n"
		pp.write(content)
	
	##create kml file from path

	with open("partition.kml","w") as ff:
		begin = '''<Placemark>
		 <name>Bleecker Street</name>
		<LineString>
		 <tessellate>1</tessellate>
		 <coordinates>\n'''
		print "---------------PATH-----------------"
		body = ""
		for item in path1:
			print item
			n = item[0]
			coord = gps[n]
			body += str(coord[1]) + "," + str(coord[0]) + "," + "0\n"

		end = '''</coordinates>
		 </LineString>
		</Placemark>'''

		filecontent = begin + body + end
		ff.write(filecontent)