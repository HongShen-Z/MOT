# from mpl_toolkits.mplot3d import axes3d
# import matplotlib.pyplot as plt
# from matplotlib import cm
# import numpy as np
#
# ax = plt.figure().add_subplot(projection='3d')
# X, Y, Z = axes3d.get_test_data(0.05)
#
# # Plot the 3D surface
# ax.plot_surface(X, Y, Z, rstride=8, cstride=8, alpha=0.3)
#
# # Plot projections of the contours for each dimension.  By choosing offsets
# # that match the appropriate axes limits, the projected contours will sit on
# # the 'walls' of the graph
# ax.contourf(X, Y, Z, zdir='z', offset=-100, cmap=cm.coolwarm)
# ax.contourf(X, Y, Z, zdir='x', offset=-40, cmap=cm.coolwarm)
# ax.contourf(X, Y, Z, zdir='y', offset=40, cmap=cm.coolwarm)
#
# ax.set(xlim=(-40, 40), ylim=(-40, 40), zlim=(-100, 100),
#        xlabel='X', ylabel='Y', zlabel='Z')
#
# plt.show()



# import numpy as np
# import matplotlib.pyplot as plt
#
# dataset = [[0, 0, 59.061], [0, 0.1, 59.219], [0, 0.2, 59.115], [0, 0.3, 59.212], [0, 0.4, 59.082], [0, 0.5, 59.114],
#            [0, 0.6, 59.185], [0, 0.7, 59.197], [0, 0.8, 59.187], [0, 0.9, 59.147], [0.1, 0, 59.876],
#            [0.1, 0.2, 59.886], [0.1, 0.4, 59.92], [0.1, 0.6, 59.911], [0.1, 0.8, 59.909], [0.1, 0.9, 57.305],
#            [0.2, 0., 59.869], [0.2, 0.2, 59.89], [0.2, 0.4, 59.918], [0.2, 0.6, 59.909], [0.2, 0.8, 57.296],
#            [0.3, 0., 59.869], [0.3, 0.2, 59.916], [0.3, 0.4, 59.923], [0.3, 0.6, 59.914], [0.3, 0.7, 57.344],
#            [0.4, 0., 59.866], [0.4, 0.2, 59.926], [0.4, 0.4, 59.92], [0.4, 0.6, 57.33], [0.5, 0., 59.871],
#            [0.5, 0.2, 59.927], [0.5, 0.4, 59.932], [0.5, 0.5, 57.321], [0.6, 0., 59.835], [0.6, 0.2, 59.919],
#            [0.6, 0.4, 57.314], [0.7, 0., 59.852], [0.7, 0.2, 59.915], [0.7, 0.3, 57.332], [0.8, 0., 59.853],
#            [0.8, 0.2, 57.271], [0.9, 0., 59.829], [0.9, 0.1, 57.187], [1., 0., 56.755]]
# dataset = np.array(dataset)
# x, y, z = dataset[:, 0], dataset[:, 1], dataset[:, 2]
#
# ax = plt.figure().add_subplot(projection='3d')
# ax.set(xlim=(0, 1), ylim=(0, 1), zlim=(56.5, 60),
#        xlabel='X', ylabel='Y', zlabel='Z')
# ax.scatter(y, x, z)
#
# plt.show()


import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import rcParams
from mpl_toolkits.mplot3d.axes3d import Axes3D  # 3D引擎

# config = {
#     "font.family":'serif',
#     "mathtext.fontset":'stix',
#     "font.serif": ['Times New Roman'],
# }
# rcParams.update(config)

matplotlib.use("pgf")
pgf_config = {
    "font.family":'serif',
    "pgf.rcfonts": False,
    "text.usetex": True,
    "pgf.preamble": [
        r"\usepackage{unicode-math}",
        r"\setmathfont{XITS Math}",
        # 这里注释掉了公式的XITS字体，可以自行修改
        r"\setmainfont{Times New Roman}",
        r"\usepackage{xeCJK}",
        r"\xeCJKsetup{CJKmath=true}",
        r"\setCJKmainfont{SimSun}",
    ],
}
rcParams.update(pgf_config)

month = [0., 0.2, 0.4, 0.6, 0.8, 1.]

dataset = [[0, 0, 59.061], [0, 0.1, 59.219], [0, 0.2, 59.115], [0, 0.3, 59.212], [0, 0.4, 59.082], [0, 0.5, 59.114],
           [0, 0.6, 59.185], [0, 0.7, 59.197], [0, 0.8, 59.187], [0, 0.9, 59.147], [0.1, 0, 59.876],
           [0.1, 0.2, 59.886], [0.1, 0.4, 59.92], [0.1, 0.6, 59.911], [0.1, 0.8, 59.909], [0.1, 0.9, 57.305],
           [0.2, 0., 59.869], [0.2, 0.2, 59.89], [0.2, 0.4, 59.918], [0.2, 0.6, 59.909], [0.2, 0.8, 57.296],
           [0.3, 0., 59.869], [0.3, 0.1, 59.897], [0.3, 0.2, 59.916], [0.3, 0.3, 59.92], [0.3, 0.4, 59.923],
           [0.3, 0.5, 59.923], [0.3, 0.6, 59.914], [0.3, 0.7, 57.344], [0.4, 0., 59.866], [0.4, 0.2, 59.926],
           [0.4, 0.4, 59.92], [0.4, 0.6, 57.33], [0.5, 0., 59.871], [0.5, 0.1, 59.921], [0.5, 0.2, 59.927],
           [0.5, 0.3, 59.931], [0.5, 0.4, 59.932], [0.5, 0.5, 57.321], [0.6, 0., 59.835], [0.6, 0.2, 59.919],
           [0.6, 0.4, 57.314], [0.7, 0, 59.852], [0.7, 0.1, 59.91], [0.7, 0.2, 59.915], [0.7, 0.3, 57.332],
           [0.8, 0., 59.853], [0.8, 0.2, 57.271], [0.9, 0., 59.829], [0.9, 0.1, 57.187], [1., 0., 56.755]]
dataset = np.array(dataset)
x, y, z = dataset[:, 0], dataset[:, 1], dataset[:, 2]

ax3 = plt.figure().add_subplot(projection='3d')

for m in month:
    ax3.bar(y[x == m],
            z[x == m] - 56.5,
            zs=m,
            zdir='x',  # 在哪个⽅向上，⼀排排排列
            alpha=0.9,  # alpha 透明度
            width=0.06)

ax3.set_xlabel(r'$\gamma$')
ax3.set_ylabel(r'$\eta$')
ax3.set_zlabel(r'MOTA')
# 获取纵坐标标签对象
zlabel = ax3.zaxis.get_label()
# 旋转纵坐标标签
zlabel.set_rotation(90)
ax3.set_zticks([0, 0.5, 1, 1.5, 2, 2.5, 3], [56.5, 57.0, 57.5, 58.0, 58.5, 59.0, 59.5])

# plt.grid()
# ax3.invert_yaxis()
# plt.gca().invert_yaxis()
# plt.gca().invert_xaxis()

plt.savefig("info.jpg", dpi=500, bbox_inches='tight')
# plt.show()

# print(y[x == month[7]])
# print(month)
# print(month == 0.7)
