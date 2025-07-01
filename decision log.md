#### Required Variables 

Crisis_ID | Crisis_Name | Crisis_Start | Crisis_End | Alliance_ID | Alliance_Name | 
Alliance_Start | Alliance_End | Alliance_Type | Active_During_Crisis | 
Member_Is_Actor | N_Members | N_Members_Actors | Members_List | Actors_List |
Crisis_Location | Geographic_Match

#### Mathematical Representation

Let $C=\{c_1,\dots ,c_N\}$ be the set of ICB crises and $A=\{a_1,\dots ,a_M\}$ the set of ATOP alliances, each with start–end dates and a set of member states coded in COW numbers.  The raw master table is the Cartesian product $C\times A$, i.e., every ordered pair $(c,a)$ of crisis and alliance.  For each pair we compute two binary indicators: (i) **temporal activation** $\delta_{\text{active}}(c,a)=1$ iff $\text{start}(a)\le \text{end}(c)\land\text{end}(a)\ge \text{start}(c)$ (the alliance existed at some point during the crisis); and (ii) **actor-membership overlap** $\delta_{\text{member}}(c,a)=1$ iff $\text{actors}(c)\cap\text{members}(a)\neq\varnothing$ (at least one alliance member was a crisis actor).  The analysis set is the subset $\Omega=\{(c,a)\in C\times A\mid\delta_{\text{active}}(c,a)=1\land\delta_{\text{member}}(c,a)=1\}$, containing only those crisis–alliance pairs where the alliance was concurrently in force **and** implicated in the crisis via membership.

