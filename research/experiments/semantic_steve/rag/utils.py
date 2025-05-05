from scipy.optimize import fsolve

# NOTE: Unfinished code to solve a system of equations to get n dimensions to broadcast
# normalized scalars (e.g., depth of current task) to for embedding concatenation based on
# a relative influence coefficient

# # The func below but w/ descriptive naming
# def func(dimensions_to_brodcast_to):
#     # out = []
#     # for i in range(len(bs)):
#     #     out.append(b[i]- (P[i] / (d + sum(b))))
#     # return out
#     out = []
#     for i in range(len(influence_factors_to_get_broadcast_dimensions_for)):
#         out.append(
#             dimensions_to_brodcast_to[i]
#             - (
#                 influence_factors_to_get_broadcast_dimensions_for[i]
#                 / (embed_dim + sum(dimensions_to_brodcast_to))
#             )
#         )
#     return out


def get_dimensions_to_broadcast_to(
    influence_factors_to_get_broadcast_dimensions_for: list[float],
    embed_dim: int,
) -> tuple[int, ...]:
    ps = influence_factors_to_get_broadcast_dimensions_for
    d = embed_dim
    est_bs = [1] * len(ps)

    def func(bs):
        out = []
        for p, b in zip(ps, bs, strict=False):
            out.append(b - (p / (d + sum(bs))))
        return out

    return fsolve(func, est_bs)


if __name__ == "__main__":
    influence_factors = [0.333]
    embed_dim = 10
    result = get_dimensions_to_broadcast_to(influence_factors, embed_dim)
    print(result)
