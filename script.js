let score = document.querySelector("#score")
let wickets = document.querySelector("#wickets")
let ball = document.querySelector("#balls")
let overs = document.querySelector("#over")

let liveRun = 0;
let out = 0;
let balls = 0;
let over = 1;




function run(n){
    
    if (n == 8){ //8 is for noBall and wide 
        liveRun += 1;
    } else if(n == 7){ //7 is for out
        balls += 1;
        out += 1;
        if(balls % 6 == 0){
            over += 1;
        }
    }else{
        liveRun += n;
        balls += 1;
        if(balls % 6 == 0){
            over += 1;
        }
    }
    
    score.innerText =  liveRun;
    wickets.innerText = out;
    ball.innerText = balls;
    overs.innerText = over;
}
