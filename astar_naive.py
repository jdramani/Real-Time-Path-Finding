try:
	import Queue as Q
except ImportError:
	import queue as Q

from collections import defaultdict
import datetime
from datetime import timedelta
import argparse
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
	dist = great_circle(gps[neighbor], gps[goal]).miles
	t = (float(dist)/float(80)) * 60 * 60 * 1000
	return t

def astar_naive(start, goal, start_time):
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
		current = openSet.get()[1]
		if current == goal:
			return reconstruct_path(cameFrom, current, time_at_this_node)

		# Do not need to do the below step as openSet.get() already removes it
		#openSet.Remove(current)
		closedSet.append(current)
		for item in graph[current]:
			neighbor = item[0]
			neighbor_costs = item[1]
			if neighbor in closedSet:
				continue		# Ignore the neighbor which is already evaluated.
			
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
				openSet.put((tentative_gScore + heuristic_cost_estimate(neighbor, goal), neighbor))
			elif tentative_gScore >= gScore[neighbor]:
				continue		# This is not a better path.

			# This path is the best until now. Record it!
			cameFrom[neighbor] = current
			gScore[neighbor] = tentative_gScore
			fScore[neighbor] = gScore[neighbor] + heuristic_cost_estimate(neighbor, goal)
			time_at_this_node[neighbor] = (cost_to_neighbor*tdelta) + curnode_time



	return -1

if __name__ == "__main__":
	path = astar_naive(source,destination,depart)
	path1 = path[:]
	path = reversed(path)
	path1 = reversed(path1)
	
	
	
	with open("naive_path.txt","w") as pp:
		content = ""
		for item in path:
			content += str(item) + "\n"
		pp.write(content)
	
	##create kml file from path

	with open("naive.kml","w") as ff:
		begin = '''<Placemark>
		 <name>Bleecker Street</name>
		<LineString>
		 <tessellate>1</tessellate>
		 <coordinates>\n'''

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