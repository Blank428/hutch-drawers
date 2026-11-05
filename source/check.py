import sys; sys.path.insert(0, '.')
from drawer_module import *
H = float(sys.argv[1]) if len(sys.argv) > 1 else 74.0
D = float(sys.argv[2]) if len(sys.argv) > 2 else 232.0
p = P(H=H, D=D)
if D < 232: p.grid_y, p.windows = 1, False
F, Dr, Fp = frame(p), drawer_assembled(p), faceplate(p)
iv = lambda a, b: (a ^ b).volume()
print(f"H={p.H} D={p.D}: drawer {p.Wd:.1f} x {p.Dd:.1f} x {p.Hd:.1f}, usable above sockets {p.usable:.1f}")
for n, m in (("frame", F), ("drawer", Dr), ("faceplate", Fp), ("tag", label_tag(p)), ("pad", tpu_pad(p)), ("cap4", tpu_cap(p, 4.0))):
    print(f"  {n:9s} ok={m.status().name} genus={m.genus()} vol={m.volume()/1000:6.2f} cm3")
for n, fn in (("frame", frame_print), ("drawer", drawer_print), ("faceplate", faceplate_print)):
    b = fn(p).bounding_box(); dims = (b[3]-b[0], b[4]-b[1], b[5]-b[2])
    print(f"  print {n:9s} {dims[0]:6.1f} x {dims[1]:6.1f} x {dims[2]:6.1f}  fits A1: {all(x <= 256 for x in dims)}")
dc, fc = place(Dr, p), place(Fp, p)
print("  closed overlaps (mm3): frame/drawer %.3f frame/face %.3f drawer/face %.3f" % (iv(F, dc), iv(F, fc), iv(Dr, Fp)))
print("  drawer sits on rails: gap drawer-frame %.3f mm (0 = touching)" % F.min_gap(dc, 2))
# drawer lifted 0.6 (ceiling contact) should be clear
print("  drawer raised by ceil_clear-0.05: overlap %.3f" % iv(F, place(Dr, p, 0, p.ceil_clear - 0.05)))
up = F.translate((0, 0, p.H))
print("  stacked flush: frame overlap %.3f, gap %.3f; faceplate overlap %.3f, reveal %.2f mm" % (iv(F, up), F.min_gap(up, 2), iv(fc, place(Fp, p, z=p.H)), fc.min_gap(place(Fp, p, z=p.H), 3)))
# faceplate must hang on the posts: moving it down 0.3 mm must collide; seated there is no overlap except the snap
print("  faceplate seated overlap %.3f mm3 (snap only); moved down 0.3: %.2f mm3; moved up 0.3: %.2f mm3" % (iv(Dr, Fp), iv(Dr, Fp.translate((0, 0, -0.3))), iv(Dr, Fp.translate((0, 0, 0.3)))))
ys = [0, 0.2, 0.4, 0.6, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8, 10, 20]
stop = p.Dd + p.standoff - p.inside_at_stop
ys += [stop - 3 + k * 0.5 for k in range(12)]
row = [f"{y:.1f}:{iv(F, place(Dr, p, y)):.1f}" for y in ys]
print("  pull sweep mm:overlap-mm3 ->", " ".join(row))
print(f"  stop expected near pull {stop:.1f} ({p.inside_at_stop:.0f} mm still inside)")
