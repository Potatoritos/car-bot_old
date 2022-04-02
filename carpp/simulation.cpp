#include <algorithm>
#include <random>
#include <vector>


namespace carpp::simulation {

std::vector<double> func_akpull(int trials, int pulls, int prob_rateup) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> distrib(1, 100);

    int amtNone = 0, amtOne = 0, amtBoth = 0, amtTotal = 0;
    
    for (int i = 0; i < trials; i++) {
        int since = 0, rateup[2] = {0};
        for (int j = 0; j < pulls; j++) {
            int prob = 2 * std::max(1, since-48);
            int r = distrib(gen);
            if (r <= prob) {
                since = 0;
                amtTotal++;
                r = distrib(gen);
                if (r <= prob_rateup)
                    rateup[r & 1]++;
            } else {
                since++;
            }
        }
        if (since == pulls) continue;

        if (!rateup[0] && !rateup[1]) amtNone++;
        else if (rateup[0] && rateup[1]) amtBoth++;
        else amtOne++;
    }

    return {
        (double)amtTotal/trials, // expected
        (double)amtNone/trials, // P(0 rateup 6*s)
        (double)(amtOne + amtBoth)/trials, // P(any rateup 6*)
        ((double)amtOne/2 + amtBoth)/trials, // P(specific rateup 6*)
        (double)amtBoth / trials // P(both rateup 6*s)
    };
}

}
