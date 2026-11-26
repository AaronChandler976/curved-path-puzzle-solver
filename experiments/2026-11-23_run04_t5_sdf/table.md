| example | detector | seed | solved | stop | iterations | planner s | s / iteration | path fine-valid | busy_frac | confounded |
|---|---|---|---|---|---|---|---|---|---|---|
| general/16505 | exact | 0 | no | iterations | 5000 | 3169 | 0.634 | - | 0.104 | True |
| general/16505 | exact | 1 | no | iterations | 5000 | 3115 | 0.623 | - | 0.016 | False |
| general/16505 | exact | 2 | no | iterations | 5000 | 2973 | 0.595 | - | 0.025 | False |
| general/16505 | learned | 0 | yes | solved | 2557 | 570 | 0.223 | - | 0.635 | True |
| general/16505 | learned | 1 | yes | solved | 1534 | 346 | 0.225 | - | 0.000 | False |
| general/16505 | learned | 2 | yes | solved | 2346 | 508 | 0.217 | - | 0.000 | False |
| puzzle/alpha | exact | 0 | no | iterations | 5000 | 3364 | 0.673 | - | 0.033 | False |
| puzzle/alpha | exact | 1 | no | iterations | 5000 | 3227 | 0.645 | - | 0.128 | True |
| puzzle/alpha | exact | 2 | no | iterations | 5000 | 3171 | 0.634 | - | 0.061 | True |
| puzzle/alpha | learned | 0 | no | iterations | 5000 | 943 | 0.189 | - | 0.000 | False |
| puzzle/alpha | learned | 1 | no | iterations | 5000 | 945 | 0.189 | - | 0.000 | False |
| puzzle/alpha | learned | 2 | no | iterations | 5000 | 930 | 0.186 | - | 0.000 | False |

| example | detector | solved / runs | mean iterations (solved) | mean planner s (all runs) |
|---|---|---|---|---|
| general/16505 | exact | 0 / 3 | 0 | 3086 |
| general/16505 | learned | 3 / 3 | 2146 | 475 |
| puzzle/alpha | exact | 0 / 3 | 0 | 3254 |
| puzzle/alpha | learned | 0 / 3 | 0 | 939 |
