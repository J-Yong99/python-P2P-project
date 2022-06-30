#!/bin/bash

# input
rm -f a.out *.JPG hw3 c??.sh r?.txt wccnt.txt
#TIMEOUT="timeout 60"
TIMEOUT=""
sleep 1
src=$1;
p0=$2;

ids=( )
names=( )
ports=( )
for kk in {0..4}
do
	ports+=( $(($p0+$kk)) );
	nid=$(($RANDOM%10+$kk*10+10));
	ids+=($nid);
	#nameprefix=$(cat /dev/urandom | tr -dc "a-fA-F0-9" | fold -w 3 | head -n 1)
	nameprefix=$(date +%s | fold -w 4 | tail -n 1)
	names+=(n$nameprefix$nid);
done
echo "Preparing Topology"

function prepareScene() {
	nbr=$1
	dst=$2
	fname=$3
	slt=$(($RANDOM%2+2))
	sltms=$slt.$(($RANDOM%1000))
	echo "sleep $sltms" > $fname
	for t in ${nbr[@]}
	do
		echo "echo @connect localhost $t" >> $fname
		echo "sleep" $(($RANDOM%2+1)) >> $fname
	done
	echo "sleep" $(($RANDOM%2+5)) >> $fname
	for d in ${dst[@]}
	do
		echo "echo @query $d" >> $fname
		echo "sleep" $(($RANDOM%2+1)) >> $fname
	done
	echo "sleep" $(($RANDOM%2+5)) >> $fname
	echo "echo @quit" >> $fname
}

nbr=(${ports[1]} ${ports[2]}) 
#dst=(${ids[4]} ${ids[2]}) 
dst=(${ids[2]} ${ids[4]}) 
prepareScene $nbr $dst c${ids[0]}.sh 

nbr=(${ports[2]}) 
#dst=(${ids[4]} ${ids[2]}) 
dst=(${ids[2]} ${ids[4]}) 
prepareScene $nbr $dst c${ids[1]}.sh 

nbr=(${ports[3]}) 
#dst=(${ids[4]} ${ids[0]}) 
dst=(${ids[0]} ${ids[4]}) 
prepareScene $nbr $dst c${ids[2]}.sh 

nbr=(${ports[1]}) 
#dst=(${ids[4]} ${ids[0]}) 
dst=(${ids[0]} ${ids[4]}) 
prepareScene $nbr $dst c${ids[3]}.sh 

nbr=(${ports[3]}) 
#dst=(${ids[1]} ${ids[0]}) 
dst=(${ids[0]} ${ids[1]}) 
prepareScene $nbr $dst c${ids[4]}.sh 


echo "Running Query: takes around 23secs"
if [[ "$src" =~ ".cpp" ]];
then
	g++ -pthread $src
	for kk in {0..4}
	do
		bash c${ids[$kk]}.sh | $TIMEOUT ./a.out ${ports[$kk]} ${ids[$kk]} ${names[$kk]} > r$kk.txt&
	done
elif [[ $src =~ ".c" ]];
then
	gcc -pthread $src 
	for kk in {0..4}
	do
		bash c${ids[$kk]}.sh | $TIMEOUT ./a.out ${ports[$kk]} ${ids[$kk]} ${names[$kk]} > r$kk.txt&
	done
elif [[ $src =~ ".java" ]];
then
	javac $src
	sleep 1
	cname=$(ls HW3*.class | sed 's/.class//')
	for kk in {0..4}
	do
		bash c${ids[$kk]}.sh | $TIMEOUT java $cname ${ports[$kk]} ${ids[$kk]} ${names[$kk]} > r$kk.txt&
	done
elif [[ $src =~ ".py" ]];
then
	for kk in {0..4}
	do
		bash c${ids[$kk]}.sh | $TIMEOUT python3 $src ${ports[$kk]} ${ids[$kk]} ${names[$kk]} > r$kk.txt&
	done
else
	echo "not supported" $src
fi

wait
echo "Programs ended"

grep "target ${ids[4]}" r0.txt | grep "name ${names[4]}" | grep "hop 3" > res.txt
grep "target ${ids[2]}" r0.txt | grep "name ${names[2]}" | grep "hop 1" >> res.txt
grep "target ${ids[4]}" r1.txt | grep "name ${names[4]}" | grep "hop 2" >> res.txt
grep "target ${ids[2]}" r1.txt | grep "name ${names[2]}" | grep "hop 1" >> res.txt
grep "target ${ids[4]}" r2.txt | grep "name ${names[4]}" | grep "hop 2" >> res.txt
grep "target ${ids[0]}" r2.txt | grep "name ${names[0]}" | grep "hop 1" >> res.txt
grep "target ${ids[4]}" r3.txt | grep "name ${names[4]}" | grep "hop 1" >> res.txt
grep "target ${ids[0]}" r3.txt | grep "name ${names[0]}" | grep "hop 2" >> res.txt
grep "target ${ids[1]}" r4.txt | grep "name ${names[1]}" | grep "hop 2" >> res.txt
grep "target ${ids[0]}" r4.txt | grep "name ${names[0]}" | grep "hop 3" >> res.txt
grep "target ${ids[4]}" r0.txt | grep "name ${names[4]}" | wc -l > wc.txt
grep "target ${ids[2]}" r0.txt | grep "name ${names[2]}" | wc -l >> wc.txt
grep "target ${ids[4]}" r1.txt | grep "name ${names[4]}" | wc -l >> wc.txt
grep "target ${ids[2]}" r1.txt | grep "name ${names[2]}" | wc -l >> wc.txt
grep "target ${ids[4]}" r2.txt | grep "name ${names[4]}" | wc -l >> wc.txt
grep "target ${ids[0]}" r2.txt | grep "name ${names[0]}" | wc -l >> wc.txt
grep "target ${ids[4]}" r3.txt | grep "name ${names[4]}" | wc -l >> wc.txt
grep "target ${ids[0]}" r3.txt | grep "name ${names[0]}" | wc -l >> wc.txt
grep "target ${ids[1]}" r4.txt | grep "name ${names[1]}" | wc -l >> wc.txt
grep "target ${ids[0]}" r4.txt | grep "name ${names[0]}" | wc -l >> wc.txt
succcnt=($(wc -l res.txt))
wccnt=($(grep -v 0 wc.txt | grep -v 1))

# show the result
echo "Result:" ${succcnt[0]} $wccnt $src

#rm -f hw3 c??.sh r?.txt ??.sh


