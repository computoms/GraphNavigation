import model as modellib
import htmlutils
import graph
import shutil
import sys, getopt
import json
import collections
import os


# Reads settings from a file
# File should contain the following JSON content:
# {
#    'input': '/path/to/input/folder',
#	 'output': '/path/to/output/folder',
#	 'templates': '/path/to/templates/folder'	
# }
def readSettingsFile(filename):
	with open(filename, "r") as file:
		settings = json.loads(file.read())

	return settings['input'], settings['output'], settings['templates'], filename

# Parse python script arguments (input, output, template or settings file)
def parseArguments(argv):
	inputFolder = ''
	outputFolder = ''
	templatesFolder = ''
	settingsFile = ''
	try:
		opts, args = getopt.getopt(argv, "hi:o:t:f:", ["input=", "output=", "templates=", "file="])
	except getopt.GetoptError:
		print('script arguments: -i <inputFolder> -o <outputFolder> -t <templatesFolder>')
		sys.exit(2)

	for opt, arg in opts:
		if opt == "-h":
			print("Usage:")
			print("python generator.py -f <settingsFile>")
			print("or")
			print("python generator.py -i <inputFolder> -o <outputFolder> -t <templatesFolder>")
			sys.exit(1)
		elif opt in ("-i", "--input"):
			inputFolder = arg
		elif opt in ("-o", "--output"):
			outputFolder = arg
		elif opt in ("-t", "--templates"):
			templatesFolder = arg
		elif opt in ("-f", "--file"):
			return readSettingsFile(arg)

	return inputFolder, outputFolder, templatesFolder, settingsFile

def main(argv):

	inputFolder, outputFolder, templatesFolder, settingsFile = parseArguments(argv)
	print("Start generating files from " + str(inputFolder) + " to " + str(outputFolder))
	print("Templates are in " + str(templatesFolder))

	filemgr = modellib.FileManager(inputFolder, outputFolder, templatesFolder)
	reader = modellib.ArticleReader(filemgr)
	graph_generator = graph.GraphGenerator(reader)
	html_generator = htmlutils.HtmlGenerator(filemgr)
	linker = modellib.FileLinker(filemgr, reader)

	def update_new_links():
		linker.create_new_files()
		linker.update_missing_links()

	def generate_sources():
		article_names = filemgr.list_changed_source()
		print(str(len(article_names)) + " articles changed.")
		for name in article_names:
			article = reader.read_article(name)
			graph_svg = graph_generator.generate(article)
			html_generator.generate_article(article, graph_svg)


	def generate_news():
		print("Generating news feed...")
		article_names = filemgr.list_source()
		articles = []
		for name in article_names:
			article = reader.read_article(name)
			articles.append(article)

		articles.sort(key=lambda x: x.publication_date, reverse=True)
		html_generator.generate_news(articles)

	def generate_fixed_pages():
		shutil.copyfile(os.path.join(filemgr.template_location, 'index.html'), filemgr.render_folder + "index.html")
		html_generator.generate_map(graph_generator.generate_full(filemgr.list_source()))
		generate_news()

	if len(filemgr.list_changed_source()) == 0:
		print('Nothing changed.')
		exit()

	update_new_links()
	generate_sources()
	generate_fixed_pages()


if __name__ == "__main__":
	main(sys.argv[1:])
