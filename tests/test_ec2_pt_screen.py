import sys, pathlib, math, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "calc_lib"))
import ec2_pt_screen as E


class T(unittest.TestCase):
    def test_two_span_udl(self):                       # hand: M_sup = -wL2/8, M_sag = 9wL2/128
        r = E.continuous_strip([0, 10, 20], [0, 1, 2], [10, 10])
        self.assertAlmostEqual(r["M_end"][0][1], -125.0, 6)
        self.assertAlmostEqual(r["M_span_extremes"][0][0], 70.3125, 3)

    def test_cantilever(self):                         # hand: M = -w c2/2
        r = E.continuous_strip([0, 2, 12], [1, 2], [10, 10])
        self.assertAlmostEqual(r["M_end"][0][1], -20.0, 6)

    def test_fctm_ecm_c32(self):                       # EC2 Table 3.1: C32/40 fctm 3.0, Ecm 33
        self.assertAlmostEqual(E.fctm(32), 3.02, 2)
        self.assertAlmostEqual(E.ecm(32) / 1000, 33.3, 1)

    def test_punching_hand(self):                      # C4 1100 mm, d 0.40, V 1864 kN, beta 1.15, interior
        r = E.punching(1864.0, 1.1, 0.40, "interior", 32, 1.134, 0.0012)
        u1 = 4 * 1.1 + 2 * math.pi * 0.8
        self.assertAlmostEqual(r["u1"], u1, 6)
        self.assertAlmostEqual(r["vEd_u1"], 1.15 * 1864 / (u1 * 0.40) / 1000, 6)
        self.assertAlmostEqual(r["vRdc_min"], 0.035 * 1.7071 ** 1.5 * 32 ** 0.5 + 0.1134, 3)

    def test_mrd_pt_only(self):                        # T = 400 mm2/m * 1000 MPa = 400 kN/m ; x = T/(0.8 fcd) 
        r = E.mrd_bonded_pt(400, 0.2, 32, 1000.0)
        self.assertAlmostEqual(r["T"], 400.0, 6)
        self.assertAlmostEqual(r["x"], 400 / (0.8 * 32 / 1.5 * 1000), 6)


if __name__ == "__main__":
    unittest.main()
