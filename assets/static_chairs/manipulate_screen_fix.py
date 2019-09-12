"""Utility function to extract coordinates from images and translate to coordinates used by the drawing function. Useful for generating pre-drawn images as reference."""
import os
import json




with open('/Users/eliasd/dev/chairs-demo-frontend/assets/static_chairs/fixed_huijie_small_screen_1.json', 'r') as f:
    test = json.loads(f.read())
    # test = test.split()
    output = {
        'x': [],
        'y': [],
        'drag': []
    }
    result = [str(int(x) - 400) for x in test['x']]
    # for x in test['x']:
        # 
        # print(x)
    test['x'] = result
    # for coord in test:
    #     print(coord)
    #     x, y = coord.split(',')
    #     output['x'].append(str(100 + int(x)))
    #     output['y'].append(str(140 + int(y)))
    #     output['drag'].append(False)


print(test)

with open("predrawn/out/huijie_1.json", 'w') as file:
    file.write(json.dumps(test))
