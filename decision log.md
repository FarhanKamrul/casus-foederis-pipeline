#### Required Variables 

Crisis_ID | Crisis_Name | Crisis_Start | Crisis_End | Alliance_ID | Alliance_Name | 
Alliance_Start | Alliance_End | Alliance_Type | Active_During_Crisis | 
Member_Is_Actor | N_Members | N_Members_Actors | Members_List | Actors_List |
Crisis_Location | Geographic_Match

#### Mathematical Representation

Let $C=\{c_1,\dots ,c_N\}$ be the set of ICB crises and $A=\{a_1,\dots ,a_M\}$ the set of ATOP alliances, each with start–end dates and a set of member states coded in COW numbers.  The raw master table is the Cartesian product $C\times A$, i.e., every ordered pair $(c,a)$ of crisis and alliance.  For each pair we compute two binary indicators: (i) **temporal activation** $\delta_{\text{active}}(c,a)=1$ iff $\text{start}(a)\le \text{end}(c)\land\text{end}(a)\ge \text{start}(c)$ (the alliance existed at some point during the crisis); and (ii) **actor-membership overlap** $\delta_{\text{member}}(c,a)=1$ iff $\text{actors}(c)\cap\text{members}(a)\neq\varnothing$ (at least one alliance member was a crisis actor).  The analysis set is the subset $\Omega=\{(c,a)\in C\times A\mid\delta_{\text{active}}(c,a)=1\land\delta_{\text{member}}(c,a)=1\}$, containing only those crisis–alliance pairs where the alliance was concurrently in force **and** implicated in the crisis via membership.


#### Extracting Required Variables from Dataset

##### ATOP

| ATOP Variable(s)              | Variable in Master Dataset |
|-------------------------------|----------------------------|
| `atopid`                      | `Alliance_ID`              |
| —                             | `Alliance_Name`            |
| `begday`, `begmo`, `begyr`    | `Alliance_Start`           |
| `endday`, `endmo`, `endyr`    | `Alliance_End`             |
| `defense`	`offense`	`neutral`	`nonagg`	`consul`                             | `Alliance_Type`            |
| `mem*` inference              | `N_Members`                |
| `mem*`                        | `Members_List`             |

#### ICB Crisis Dataset

| icb variable(s)                   | Variable in Master Dataset |
|-----------------------------------|----------------------------|
| `crisno`                          | `Crisis_ID`               |
| `crisname`                        | `Crisis_Name`             |
| `yrtrig`, `motrig`, `datrig` > ICB1     | `Crisis_Start`            |
| `yrterm`, `moterm`, `daterm` > ICB1     | `Crisis_End`              |
| `geog`                            | `Crisis_Location`         |
| `cracid`                          | `Actor_List`              |
| Instances of same  `crisno`       | `N_Members_Actor`         |


* For actors, notice how many crises involve multiple actors, and hence have duplicate crisis numbers, each with entry by a specific actor.

* MAIN QUESTION: Are all other variables same except cracid and actor, for all entries with the same crisno? If different, which entries are different?
* Introduce an exploratory task for this, before proceeding to merge the datasets.
* Also check if every crisno maps to a single geog value.

#### Issues that arose:

1. ICB2: Serbia and Yugoslavia have the same `cracid`.
2. ICB2: Iran's `actloc` (actor location) is mapped to Middle East (13) about 15 times, but in 5 cases, `actloc` is marked as South Asia (15). The geographic location of the actor needs to be consistent; the `geog` variable already acts as the indicator for crisis location.
3. Each actor has different crisis enter dates and exit dates, so the `Crisis_Start` and `Crisis_End` dates are codified using the system-level ICB1 dataset.
4.  Found 9 crises with multiple geog values:

| Crisis ID | Crisis Name                               | Distinct `geog` Values |
|-----------|-------------------------------------------|------------------------|
| 21        | Karl’s Return, Hungary (1921)             | 31.0, 35.0             |
| 300       | Raids on ZIPRA (1979)                     | 22.0, 24.0             |
| 307       | Rhodesia Settlement (1979)                | 22.0, 23.0             |
| 365       | South Africa Cross-Border Raid (1986)     | 23.0, 22.0             |
| 427       | US Embassy Bombings (1998)                | 13.0, 22.0, 21.0       |
| 434       | Afghanistan / US (2001)                   | 13.0, 41.0             |
| 460       | Chad–Sudan V (2009)                       | 24.0, 21.0             |
| 466       | Sudan–South Sudan (2011)                  | 21.0, 22.0             |
| 499       | Galwan Valley Border Clash (2020)         | 13.0, 11.0             |




#### ALLIANCE NAMES NOT FOUND YET

