from color_base import Bucket
from color_base import mergeWith
from colormath_fast.color_diff import delta_e_cie2000
import math
import Image
import collections
import heapq

hashes = {}

def createThumbnails(d):
	thumbs = collections.defaultdict(str)
	for name in d:
		im = Image.open(name)
		th = im.resize((50, 50))
		thumbs[name] = th
	return thumbs

def generateImage(labels, thumbs, size):
	thumbSize = (50, 50)
	labelWidth = len(labels)
	im = Image.new("RGBA", (thumbSize[0]*size[0], thumbSize[1]*size[1]))
	
	for x in range(labelWidth):
		if x % 25 == 0:
			print x / float(labelWidth)
		for y in range(len(labels[x])):
			box = (x * thumbSize[0], y * thumbSize[1])
			im.paste(thumbs[labels[x][y]], box)
			
	return im

def selectBestImage(db, colors):
	global hashes
	rgba = colors[0].getRGBA(1)
	if rgba in hashes.keys():
		return hashes[rgba]

	colorHeap = [ (delta_e_cie2000(colors[0].col, sample[1][0].col) * sample[1][0].proportion, 1, sample) for sample in db ]
	heapq.heapify(colorHeap)
	
	small = heapq.heappop(colorHeap)
	while small[1] < len(small[2][1]):
		dist = small[0]
		count = small[1]
		sample = small[2]
		bucket = sample[1][count]
		dist += delta_e_cie2000(colors[0].col, bucket.col) * bucket.proportion
		new = (dist, count+1, sample)
		small = heapq.heappushpop(colorHeap, new)

	hashes[rgba] = small[2][0]
	return small[2][0]

def createMosaic(db, photo_filename):
	im = Image.open(photo_filename)
	pix = im.load()
	size = im.size
	print size
	
	labels = [[None for x in range(size[1])] for y in range(size[0])]
	d = collections.defaultdict(int)
	
	for x in range(size[0]):
		if x % 25 == 0:
			print x / float(size[0])
		for y in range(size[1]):
			(r,g,b) = im.getpixel((x,y))
			pix = [ Bucket(r,g,b) ]
			bestSample = selectBestImage(db, pix)
			d[bestSample] += 1
			labels[x][y] = bestSample
	
	print "Building photo"
	thumbs = createThumbnails(d)
	result = generateImage(labels, thumbs, size)
	return result


def getInverseWeightedAverage(x, y, neighbors):
	totalDist = 0
	buckets = []
	for (n_x, n_y, (r,g,b)) in neighbors:
		xDif = x - n_x
		yDif = y - n_y
		dist = math.sqrt(xDif*xDif + yDif*yDif)
		totalDist += dist
		buckets.append( (Bucket(r,g,b), dist) )

	for (bucket, dist) in buckets:
		if dist == 0:
			bucket.count = 1
		else:
			bucket.count = (totalDist - dist) / dist

	return reduce(mergeWith, [bucket for (bucket, dist) in buckets])

def generateImageHex(labels, thumbs, size):
	thumbSize = (50, 50)
	labelWidth = len(labels)
	im = Image.new("RGBA", (thumbSize[0]*size[0], thumbSize[1]*size[1]))

	for (x, y, name) in labels:
		box = (int(math.floor(x * thumbSize[0])), int(math.floor(y * thumbSize[1])))
		im.paste(thumbs[name], box)

	return im

def createMosaicHex(db, photo_filename):
	im = Image.open(photo_filename)
	pix = im.load()
	size = im.size
	print size

	labels = []
	d = collections.defaultdict(int)

	x_start = 0.5
	y_range = [i*0.5*math.sqrt(3) for i in range(int(math.floor(size[1] / (0.5*math.sqrt(3))))) ]
	for y in y_range:
		if (x_start == 0.5):
			x_start = 0
		else:
			x_start = 0.5
		x_range = [x_start + i for i in range(size[0]-1)]
		for x in x_range:
			x_floor = math.floor(x)
			x_ceil = math.ceil(x)
			y_floor = math.floor(y)
			y_ceil = math.ceil(y)
			neighbors = [(x_floor, y_floor, im.getpixel((x_floor, y_floor))),
			 			 (x_floor, y_ceil, im.getpixel((x_floor, y_ceil)) ),
			 			 (x_ceil, x_floor, im.getpixel((x_ceil, y_floor))),
 			 			 (x_ceil, y_ceil, im.getpixel((x_ceil, y_ceil)) )]
			ave_color = getInverseWeightedAverage(x, y, neighbors)
			bestSample = selectBestImage(db, [ave_color])
			d[bestSample] += 1
			labels.append((x,y,bestSample))

	print "Building photo"
	thumbs = createThumbnails(d)
	result = generateImageHex(labels, thumbs, size)
	return result