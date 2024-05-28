function openPopup() {
    document.getElementById("myPopup").style.display = "flex";
    
}

function closePopup() {
    $("#myPopup").css("display", "none");
}

function save() {
    let name = $("#name_title").val();
    if (!name) {
        return alert("Nama belum di masukan !")
    }
    let email = $("#email_title").val();
    if (!email) {
        return alert("Email belum dimasukan !")
    }
    let number = $("#number_phone").val();
    if (!number) {
        return alert("Number belum dimasukan !")
    }

    let subject = $("#subject").val();
    if (!subject) {
        return alert("Subject belum dimasukan !")
    }

    let message = $("#message").val();
    if (!message) {
        return alert("Message belum dimasukan !")
    }

    let form_data = new FormData();

    form_data.append("name", name);
    form_data.append("email", email);
    form_data.append("number", number);
    form_data.append("subject", subject);
    form_data.append("message", message);

    $.ajax({
        type: "POST",
        url: "/feedback",  
        data: form_data,
        contentType: false,
        processData: false,
        success: function (response) {
            alert(response['msg']);
            window.location.reload();
        },
    });
}



