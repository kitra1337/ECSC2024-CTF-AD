from tqdm import trange

p = 32993028718791676799062280315466580754431
F = GF(p)
E = EllipticCurve(F, [1,0])
G = E.gens()[0]
n = E.order()
factors = list(factor(n))

for l, e in factors:
    fac = l^e
    cof = n//fac
    G1 = cof*G
    G2 = G1
    with open(f"dlog_{fac}", "w") as wf:
        for i in trange(1, fac):
            Px, Py = G2.xy()
            wf.write(f"{Px} {Py} {i}\n")
            G2 += G1
