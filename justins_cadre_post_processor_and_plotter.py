import pprint

import sqlite3
from cPickle import dumps, loads, HIGHEST_PROTOCOL, UnpicklingError, load, dump
import numpy as np 

from matplotlib import pylab



def get_data(db_file_name):

    conn = sqlite3.connect(db_file_name)
    conn.text_factory = sqlite3.OptimizedUnicode
    cur = conn.cursor()


    sql_count = "SELECT count(*) from cases"
    print "total cases:",  [x for x in cur.execute(sql_count)][0][0]

    sql_count = 'SELECT case_id from casevars where name=="Objective_0"'
    ids = [x[0] for x in cur.execute(sql_count)]

    id_index_map = dict([(id,i) for i,id in enumerate(ids)])
    n_cases = len(ids)
    print "top level cases:", n_cases
    data = {}

    sql = "SELECT var_id,name,case_id,sense,value FROM cases INNER JOIN casevars ON casevars.case_id=cases.id WHERE case_id in (%s)"%','.join(map(str,ids))

    cur = conn.cursor()
    cur.execute(sql)

    objective_cases = []
    for var_id, vname, case_id, sense, value in cur: 
        if not isinstance(value, (float, int, str)):
            try:
                value = loads(str(value))
            except UnpicklingError as err:
                raise UnpicklingError("can't unpickle value '%s' for"
                                      " case '%s' from database: %s"
                                      % (vname, case_id, str(err)))

        index = id_index_map[case_id]
        if vname in data: 
            data[vname][index] = value
        else: 
            data[vname]=[None,]*n_cases
            data[vname][index] = value 

    return n_cases,data


if __name__ == "__main__": 

    vars_name = {
        "Data": 1e3,
        "Gamma": np.pi/180., 
        "SOC": 1e-2, 
        "P_comm": 1/5., 
        'Comm_BitRate.gain': 1., 
        "CommLOS": 1., 
        "LOS": 1.,    
    }

    n_cases_prune, data_prune = get_data('CADRE-with-pruning.db')
    #n_cases_prune, data_prune = get_data('CADRE.db')
    n_cases_full, data_full = get_data('CADRE-no-pruning.db')
    #n_cases_full, data_full = get_data('CADRE.db')

    #pprint.pprint(data.keys()); exit()

    time = data_prune['pt0.t'][0]/3600.


    iters = [0]

    for iter_index in iters: 
        for mp_index in xrange(6):
            for var, s in vars_name.iteritems(): 
                d = data_prune['pt%d.%s'%(mp_index,var)][iter_index]
                #print var, d/s

                output = np.empty((2,time.shape[0]))
                output[0,:] = time
                output[1,:] = d/s

                np.savetxt('postproc_results/%s_%d-%d.dat'%(var,iter_index,mp_index), output.T)


    times = np.array(data_prune['timestamp'])
    t0,t1 = times[3:n_cases_prune-1], times[4:]
    avg_time = np.average(t1-t0)

    print "averge time per case: ", avg_time
    # print "Total time: ", (times[324]-times[0])/3600.

   

#######################

    # pylab.figure()
    # pylab.plot(seconds_per_case, label="individual")
    # pylab.plot(avg_seconds_per_case, label="average")
    # pylab.legend(loc="best")
    # pylab.title('Case Computational Cost')
    # pylab.xlabel('Iteration #')
    # pylab.ylabel('Time (sec)')

    # Z = np.array(Z)
    # if not len(Z):
    #     print "no data yet..."
    #     quit()

    pylab.rcParams['text.latex.preamble']=[r"\usepackage{lmodern}"]
    params = {
        'font.size': 15, 
        'font': 'serif', 
        'font.family': "lmodern",
        'text.latex.unicode': True,
    }
    pylab.rcParams.update(params)

    sum_data_prune = np.sum(np.array([np.array(data_prune['pt%d.Data'%i])[:,0,-1] for i in xrange(6)]), axis=0)
    sum_data_full = np.sum(np.array([np.array(data_full['pt%d.Data'%i])[:,0,-1] for i in xrange(6)]), axis=0)


    print data_prune['pt0.CP_Isetpt']
    exit()

    print "Final optimum 326: ", sum_data_full[n_cases_prune-1]/8.
    print "Final optimum: ", sum_data_full[-1]/8.
    print "Final optimum: ", sum_data_prune[-1]/8., sum_data_prune[100]/8.

    fig = pylab.figure()
    pylab.subplot(211)


    pylab.title("Total Data")
    pylab.axhline(y=sum_data_full[n_cases_prune-1], ls="dashed", c="r")
    pylab.axhline(y=sum_data_full[-1], ls="dashed", c="m")
    pylab.plot(sum_data_full[:n_cases_prune], 'b', label="Full-graph")
    pylab.plot(sum_data_prune, 'g', label="Reduced-graph")
    pylab.legend(loc="best")
    #pylab.plot([0, len(sum_data)], [3e4, 3e4], 'k--', marker="o")
    pylab.ylabel('Gigabits')
    pylab.ticklabel_format(style='sci', axis='y', scilimits=(0,0))


    constraints = ["Constraint ( pt%(i)d.ConCh<=0 )", 
                   "Constraint ( pt%(i)d.ConDs<=0 )", 
                   "Constraint ( pt%(i)d.ConS0<=0 )",
                   "Constraint ( pt%(i)d.ConS1<=0 )",
                   "Constraint ( pt%(i)d.SOC[0][0]=pt%(i)d.SOC[0][-1] )"
                   ]

    c_data_prune = []
    c_data_full = []
    for con in constraints: 
        d = np.array([np.array(data_prune[con%{'i':i}])[:,0] for i in xrange(6)])
        #d = np.sum(np.ma.masked_outside(d,0,10000)**2,axis=0)**.5
        #d = np.sum(d**2,axis=0)**.5
        d = np.max(d,axis=0)
        c_data_prune.append(d)

        d = np.array([np.array(data_full[con%{'i':i}])[:,0] for i in xrange(6)])
        #d = np.sum(np.ma.masked_outside(d,0,10000)**2,axis=0)**.5
        #d = np.sum(d**2,axis=0)**.5
        d = np.max(d,axis=0)
        c_data_full.append(d)


    pylab.subplot(212)
    #pylab.title(r"$\left|\left|Constraints\right|\right|_2$")
    pylab.title(r"Max Constraint Violation")
    #pylab.plot([0, n_cases], [0, 0], 'k--')
    #pylab.semilogy(c_data[0], label=r"$I_{bat} - 5 \leq 0$", c='b')
    # pylab.semilogy(c_data[1], label=r"$-10 - I_{bat} \leq 0$", c='g')
    # pylab.semilogy(c_data[2], label=r"$0.2 - SOC \leq 0$", c='r')
    # pylab.semilogy(c_data[3], label=r"$SOC - 1 \leq 0$", c='c')
    # pylab.semilogy(c_data[4], label=r"$fSOC - iSOC = 0$", c='m')
    pylab.semilogy(np.max(c_data_full, axis=0)[:n_cases_prune], c='b')
    pylab.semilogy(np.max(c_data_prune, axis=0), c='g')
    pylab.ylim(1e-4,1e2)

    #pylab.legend(loc="best")
    pylab.legend(bbox_to_anchor=[1.11,1.26] ,loc="upper right")

    pylab.xlabel("Iteration #")

    fig.set_size_inches(10,7)
    fig.tight_layout()
    pylab.savefig('cadre_opt_progress.pdf', dpi=1000, bbox_inches="tight")


