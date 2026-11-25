// GardenNode-C6 outdoor enclosure (print in ASA or PETG, 0.2 mm layers, 4 walls, 25% infill)
// part = "base" | "lid" | "usb_plug" | "assembly"
part = "assembly";
$fn = 64;

// ---- PCB (rev A) ----
pcb_w = 100; pcb_h = 82; pcb_t = 1.6;
pcb_holes = [[4,4],[96,4],[4,78],[96,78]];     // PCB frame: x right, y down from top edge
standoff_h = 6;

// ---- box ----
wall = 2.6; floor_t = 2.6; lid_t = 3.0;
in_x = 108; in_y = 100; in_z = 36;              // cavity
out_x = in_x + 2*wall; out_y = in_y + 2*wall; out_z = floor_t + in_z;
corner_r = 5;
pcb_ox = 2.0; pcb_oy = (in_y - pcb_h)/2;   // PCB sits 2 mm from the USB wall: receptacle face ~1.5 mm behind the inner wall
boss_d = 8; boss_hole = 2.6;                     // M3 self-tapping (or 4.0 for heat-set inserts)
groove_w = 2.2; groove_d = 1.6;                  // for 2 mm silicone cord gasket
tongue_w = 1.4; tongue_h = 1.3;

// PCB frame -> box frame (cable/connector edge of PCB faces box -Y wall)
function pb(p) = [wall + pcb_ox + p[0], wall + pcb_oy + (pcb_h - p[1])];
pcb_top_z = floor_t + standoff_h + pcb_t;

// external features
gland_d = 12.6;                                  // PG7 cable gland thread
gland_x = [pb([18,0])[0], pb([60,0])[0], pb([88,0])[0]];
gland_z = floor_t + in_z*0.52;
usb_c = [0, pb([0,14])[1], pcb_top_z + 1.6];     // centre of USB-C on -X wall
vent_x = pb([39,0])[0];

module rbox(x, y, z, r) {
    hull() for (i=[r, x-r], j=[r, y-r]) translate([i, j, 0]) cylinder(r=r, h=z);
}
boss_pos = [[wall+boss_d/2-0.5, wall+boss_d/2-0.5], [out_x-wall-boss_d/2+0.5, wall+boss_d/2-0.5],
            [wall+boss_d/2-0.5, out_y-wall-boss_d/2+0.5], [out_x-wall-boss_d/2+0.5, out_y-wall-boss_d/2+0.5]];

module base() {
    difference() {
        union() {
            difference() {
                rbox(out_x, out_y, out_z, corner_r);
                translate([wall, wall, floor_t]) rbox(in_x, in_y, in_z + 1, corner_r - wall + 0.5);
            }
            // lid screw bosses
            for (b = boss_pos) translate([b[0], b[1], 0]) cylinder(d=boss_d, h=out_z);
            // PCB standoffs
            for (h = pcb_holes) let(p = pb(h)) translate([p[0], p[1], 0]) cylinder(d=7, h=floor_t + standoff_h);
            // mounting ears (post / fence mount), M5 / #10 screws
            for (sx = [-1, 1]) for (y = [out_y*0.25, out_y*0.75])
                translate([sx < 0 ? -9 : out_x - 3, y - 8, 0]) difference() {
                    cube([12, 16, 4]);
                }
            // strap ribs on the back for hose clamps / zip ties
        }
        // boss + standoff holes
        for (b = boss_pos) translate([b[0], b[1], 8]) cylinder(d=boss_hole, h=out_z);
        for (h = pcb_holes) let(p = pb(h)) translate([p[0], p[1], 1.2]) cylinder(d=2.6, h=20);
        // ear holes
        for (sx = [-1, 1]) for (y = [out_y*0.25, out_y*0.75])
            translate([sx < 0 ? -3.5 : out_x + 3.5, y, -1]) cylinder(d=5.5, h=10);
        // gasket groove in rim
        translate([0, 0, out_z - groove_d]) difference() {
            translate([wall/2 - groove_w/2, wall/2 - groove_w/2, 0]) rbox(out_x - wall + groove_w, out_y - wall + groove_w, groove_d + 1, corner_r - wall/2 + groove_w/2);
            translate([wall/2 + groove_w/2, wall/2 + groove_w/2, -1]) rbox(out_x - wall - groove_w, out_y - wall - groove_w, groove_d + 3, corner_r - wall/2 - groove_w/2);
            for (b = boss_pos) translate([b[0], b[1], -1]) cylinder(d=boss_d + 0.01, h=5);
        }
        // cable glands (bottom wall when mounted, -Y)
        for (x = gland_x) translate([x, -1, gland_z]) rotate([-90, 0, 0]) cylinder(d=gland_d, h=wall + 2);
        // pressure-equalisation vent: 5 mm hole, 12.5 mm recess for adhesive ePTFE vent
        translate([vent_x, -1, gland_z]) rotate([-90, 0, 0]) cylinder(d=5, h=wall + 2);
        translate([vent_x, -0.01, gland_z]) rotate([-90, 0, 0]) cylinder(d=12.8, h=0.6);
        // USB-C service port on -X wall (closed with TPU plug)
        // sized for a USB-C plug overmold (up to 13 x 7.5 mm) so the plug seats fully
        translate([-1, usb_c[1], usb_c[2]]) rotate([0, 90, 0]) hull() for (d = [-2.75, 2.75]) translate([0, d, 0]) cylinder(d=7.5, h=wall + 2);
        // reset / boot access is through the lid (not needed in normal use)
        // label
        translate([out_x/2, 6, 0.6]) rotate([180, 0, 0]) linear_extrude(1) text("GardenNode-C6", size=6, halign="center", valign="center");
    }
}

module lid() {
    difference() {
        union() {
            rbox(out_x, out_y, lid_t, corner_r);
            // tongue pressing into gasket groove (printed facing up, flip for install)
            translate([0, 0, lid_t]) difference() {
                translate([wall/2 - tongue_w/2, wall/2 - tongue_w/2, 0]) rbox(out_x - wall + tongue_w, out_y - wall + tongue_w, tongue_h, corner_r - wall/2 + tongue_w/2);
                translate([wall/2 + tongue_w/2, wall/2 + tongue_w/2, -1]) rbox(out_x - wall - tongue_w, out_y - wall - tongue_w, tongue_h + 2, corner_r - wall/2 - tongue_w/2);
                for (b = boss_pos) translate([b[0], b[1], -1]) cylinder(d=boss_d + 0.6, h=5);
            }
            // locating lip inside the cavity
            translate([0, 0, lid_t]) difference() {
                translate([wall + 0.3, wall + 0.3, 0]) rbox(in_x - 0.6, in_y - 0.6, 3, corner_r - wall);
                translate([wall + 2, wall + 2, -1]) rbox(in_x - 4, in_y - 4, 5, corner_r - wall);
                for (b = boss_pos) translate([b[0], b[1], -1]) cylinder(d=boss_d + 1.2, h=6);
            }
        }
        for (b = boss_pos) translate([b[0], b[1], -1]) {
            cylinder(d=3.4, h=lid_t + 5);
            cylinder(d=6.2, h=1.6);                         // pan-head recess
        }
        // drip-edge text (top surface is z=0 face after flipping)
        translate([out_x/2, out_y/2, -0.01]) mirror([0, 1, 0]) linear_extrude(0.6) text("GardenNode", size=9, halign="center", valign="center");
    }
}

module usb_plug() {   // print in TPU 95A - press-fit weather plug for the USB-C opening
    hull() for (d = [-2.75, 2.75]) translate([0, d, 0]) cylinder(d=7.6, h=wall + 0.4);
    translate([0, 0, -1.6]) hull() for (d = [-4.5, 4.5]) translate([0, d, 0]) cylinder(d=11, h=1.6);
    translate([-2, 9, -1.6]) cube([4, 10, 1.2], center=false);
}

module pcb_ghost() {
    color("green") translate([wall + pcb_ox, wall + pcb_oy, floor_t + standoff_h]) cube([pcb_w, pcb_h, pcb_t]);
    color("silver") translate([wall + pcb_ox + 50 - 38.5, pb([0, 45])[1] - 10.3, pcb_top_z]) cube([77, 20.6, 15]);
    color("royalblue") translate([wall + pcb_ox + 50 - 33, pb([0, 45])[1], pcb_top_z + 9.6]) rotate([0, 90, 0]) cylinder(d=18.4, h=66);
}

if (part == "base") base();
else if (part == "lid") translate([0, 0, 0]) lid();
else if (part == "usb_plug") usb_plug();
else {
    base(); pcb_ghost();
    translate([0, out_y, out_z + lid_t + 15]) rotate([180, 0, 0]) lid();
}
