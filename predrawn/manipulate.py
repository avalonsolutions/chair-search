"""Utility function to extract coordinates from images and translate to coordinates used by the drawing function. Useful for generating pre-drawn images as reference."""
import os
import json




with open('/Users/eliasd/dev/chairs-demo-frontend/predrawn/coords3.txt', 'r') as f:
    test = f.read()
    test = test.split()
    output = {
        'x': [],
        'y': [],
        'drag': []
    }
    for coord in test:
        print(coord)
        x, y = coord.split(',')
        output['x'].append(str(500 + int(x)))
        output['y'].append(str(140 + int(y)))
        output['drag'].append(False)


print(output)

with open("predrawn/out/auto_draw_chair_3.json", 'w') as file:
    import json
    file.write(json.dumps(output))
