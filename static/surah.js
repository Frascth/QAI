



// $(document).ready(function()
// {
    canplay = true;
    console.log("ready")

    let audios = document.getElementsByTagName('audio');
    let play = document.getElementById("play");
    let prev = document.getElementById("prev");
    let next = document.getElementById("next");
    let lbl_ayah = document.getElementById("ayah");
    index = 0;
    isplaying = false;

    next.disabled = false;

    for (let i = 0, j = audios.length; i < j-1; i++)
    {
        if (i==j-2)
        {
            audios[i].addEventListener("ended", e => {
                next.disabled = true
                prev.disabled = false
                index +=1;
                lbl_ayah.textContent = index+1
                audios[index].play();
            });
        }
        else
        {
            audios[i].addEventListener("ended", e => {
                prev.disabled = false
                index +=1;
                lbl_ayah.textContent = index+1
                audios[index].play();
            });
        }
    }

    audios[audios.length-1].addEventListener("ended", e => {
        next.disabled = false;
        prev.disabled = true;
        index =0;
        lbl_ayah.textContent = "1"
        play.textContent = "Play"
    });

    play.onclick = function()
    {
        if (!isplaying && canplay)
        {
            audios[index].play();
            play.textContent = "Pause";
            isplaying = true;
        }
        else
        {
            audios[index].pause();
            play.textContent = "Play";
            isplaying = false;
        }
    }

    prev.onclick = function()
    {
        if (index>0 && canplay)
        {
            play.textContent = "Pause";
            next.disabled = false;
            audios[index].pause();
            audios[index].currentTime = 0;
            index-=1;
            if (index<=0)
            {
                prev.disabled = true;
            }
            lbl_ayah.textContent = index+1;
            audios[index].play();
        }
    }

    next.onclick = function()
    {
        if (index<audios.length-1 && canplay)
        {
            isplaying = true;
            play.textContent = "Pause"
            prev.disabled = false;
            audios[index].pause();
            audios[index].currentTime = 0;
            index+=1;
            if (index>=audios.length-1)
            {
                next.disabled = true;
            }
            lbl_ayah.textContent = index+1;
            audios[index].play();
        }
    }

    function gopause(){
        audios[index].pause();
        play.textContent = "Play";
        play.disabled = true;
        prev.disabled = true;
        next.disabled = true;

    }
// });

var device = navigator.mediaDevices.getUserMedia({audio: true});
var items = [];

var num = 0;
var lst_read = 999;
var b64 = "default";

var canplay = true;

function chng(id){
    var btnrec = document.getElementById("btnrec"+id.toString());
    var btnstop = document.getElementById("btnstop"+id.toString());
    btnrec.disabled= !btnrec.disabled;
    btnstop.disabled= !btnstop.disabled;

    if (btnrec.textContent == "Record"){
        gopause();
        canplay = false;
        btnrec.textContent = "AI listening";
        let t = ["AI listening", "AI listening.", "AI listening..", "AI listening..."]
        let i = 0;
        // let btn = "btnrec"+id.toString();

        setInterval(function(){
            btnrec.textContent = t[(i=(i+1)%t.length)];
        }, 1000)
    }
    else{
        btnrec.textContent == "Record";
    }

}

function binreader(blob){

    var reader = new FileReader();
    reader.readAsDataURL(blob); 
    reader.onload = function(){
        window.b64 = reader.result.replace(/^data:.+;base64,/, '');
        var aud = document.getElementById("aud"+num.toString());
        var ayah = document.getElementById("ayah"+num.toString());
        var form = document.getElementById("ayah-"+num.toString());
        var inp_lread = document.getElementById("inp_lread"+num.toString());

        aud.value = b64;
        ayah.value = num;
        inp_lread.value = lst_read;
        // console.log(inp_lread.value)
        form.submit();

        // console.log(num, start_ayah);
        // aud[num-start_ayah].value = b64;
        // ayah[num-start_ayah].value = num;

        // ayah_form[num-start_ayah].submit();
    }

}

function rec(){
    // var btnrec = document.getElementById("btnrec"+id.toString());
    // var btnstop = document.getElementById("btnstop"+id.toString());
    // btnrec.disabled=true;
    // btnstop.disabled=false;
    
    items = []
    device.then( stream => {
        recorder = new MediaRecorder(stream);
        recorder.start();
        recorder.ondataavailable = e=>{
            items.push(e.data);
            recorder.addEventListener("stop", e =>{
                var blob = new Blob(items, {type: 'audio/webm'});
                binreader(blob);
            })
        }
    })
}

function stopp(val){

    // var btnrec = document.getElementById("btnrec"+id.toString());

    // btnrec.textContent = "Evaluating";
    // let t = ["Evaluating", "Evaluating.", "Evaluating..", "Evaluating..."]

    // setInterval(function(){
    //     btnrec.textContent = t[(i=(i+1)%t.length)];
    // }, 1000)

    canplay = true;
    num = val;
    lst_read = 999; //backend detect on 1 or 0

    recorder.stop();

}